"""
Management command para gestionar la expiración automática de reservas

Este comando debe ejecutarse periódicamente (cada hora) para:
1. Enviar recordatorios de pago 48-72h antes del límite
2. Cancelar reservas que expiraron (72h antes del vuelo)
3. Eliminar reservas 24h antes del vuelo si no se pagaron

Configuración recomendada en crontab:
0 * * * * cd /path/to/project && python manage.py expiracion_reservas

O con Celery Beat:
CELERY_BEAT_SCHEDULE = {
    'expiracion-reservas': {
        'task': 'reservas.tasks.verificar_expiracion_reservas',
        'schedule': crontab(minute=0),  # cada hora
    },
}
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from datetime import timedelta
import logging

# Configurar logging específico para este comando
logger = logging.getLogger('reservas.expiracion')


class Command(BaseCommand):
    help = 'Gestiona la expiración automática de reservas según las reglas de 72h/24h'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecuta en modo simulación sin realizar cambios reales',
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Muestra información detallada de cada reserva procesada',
        )
        
        parser.add_argument(
            '--send-emails',
            action='store_true',
            help='Envía emails de recordatorio y notificación (requiere configuración SMTP)',
        )
        
        parser.add_argument(
            '--force-email',
            action='store_true',
            help='Fuerza el envío de emails incluso si ya se enviaron antes',
        )
        
        parser.add_argument(
            '--limite-procesamiento',
            type=int,
            default=100,
            help='Máximo número de reservas a procesar por ejecución (default: 100)',
        )
        
        parser.add_argument(
            '--reserva-especifica',
            type=str,
            help='Procesar solo una reserva específica por su código',
        )

    def handle(self, *args, **options):
        """Punto de entrada principal del comando"""
        
        # Configurar opciones
        self.dry_run = options['dry_run']
        self.verbose = options['verbose']
        self.send_emails = options['send_emails']
        self.force_email = options['force_email']
        self.limite = options['limite_procesamiento']
        self.reserva_especifica = options['reserva_especifica']
        
        # Mostrar inicio
        now = timezone.now()
        self.stdout.write(
            self.style.SUCCESS(f'=== INICIANDO VERIFICACIÓN DE EXPIRACIÓN DE RESERVAS ===')
        )
        self.stdout.write(f'Fecha y hora: {now.strftime("%d/%m/%Y %H:%M:%S")}')
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING('🚨 MODO DRY-RUN: No se realizarán cambios reales')
            )
        
        if not self.send_emails:
            self.stdout.write(
                self.style.WARNING('📧 Emails deshabilitados (use --send-emails para habilitar)')
            )
        
        # Verificar configuración de email
        if self.send_emails and not self._verificar_config_email():
            self.stdout.write(
                self.style.ERROR('❌ Configuración de email incompleta. Se deshabilitarán los emails.')
            )
            self.send_emails = False
        
        # Inicializar estadísticas
        self.stats = {
            'procesadas': 0,
            'eliminadas': 0,
            'canceladas': 0,
            'recordatorios_enviados': 0,
            'notificaciones_cancelacion': 0,
            'errores': 0,
            'ya_procesadas': 0
        }
        
        try:
            # Ejecutar procesamiento
            if self.reserva_especifica:
                self._procesar_reserva_especifica()
            else:
                self._procesar_reservas_masivo()
            
            # Mostrar reporte final
            self._mostrar_reporte_final()
            
        except Exception as e:
            logger.error(f'Error crítico en comando de expiración: {e}', exc_info=True)
            raise CommandError(f'Error ejecutando comando: {e}')

    def _verificar_config_email(self):
        """Verifica que la configuración de email esté completa"""
        try:
            email_backend = getattr(settings, 'EMAIL_BACKEND', None)
            email_host = getattr(settings, 'EMAIL_HOST', None)
            default_from = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
            
            if not email_backend or 'console' in email_backend.lower():
                return False
                
            if not email_host or not default_from:
                return False
                
            return True
            
        except Exception:
            return False

    def _procesar_reserva_especifica(self):
        """Procesa una reserva específica por código"""
        from reservas.models import Reserva
        
        try:
            reserva = Reserva.objects.get(
                codigo_reserva=self.reserva_especifica,
                activo=True
            )
            
            self.stdout.write(f'Procesando reserva específica: {reserva.codigo_reserva}')
            resultado = self._procesar_reserva_individual(reserva)
            self.stdout.write(f'Resultado: {resultado}')
            
        except Reserva.DoesNotExist:
            raise CommandError(f'Reserva {self.reserva_especifica} no encontrada o no activa')

    def _procesar_reservas_masivo(self):
        """Procesa reservas de forma masiva"""
        from reservas.models import Reserva
        
        now = timezone.now()
        
        # Obtener reservas que necesitan procesamiento
        queryset = Reserva.objects.filter(
            activo=True,
            estado__in=[
                Reserva.EstadoChoices.CREADA,
                Reserva.EstadoChoices.RESERVADO_SIN_PAGO
            ],
            vuelo__fecha_salida_estimada__gt=now - timedelta(hours=24),  # No procesar vuelos ya pasados
            fecha_limite_pago__isnull=False
        ).select_related('pasajero', 'vuelo__origen_principal', 'vuelo__destino_principal')
        
        # Aplicar límite
        if self.limite:
            queryset = queryset[:self.limite]
        
        total_reservas = queryset.count()
        
        if total_reservas == 0:
            self.stdout.write(
                self.style.SUCCESS('✅ No hay reservas que requieran procesamiento')
            )
            return
        
        self.stdout.write(f'📋 Encontradas {total_reservas} reservas para procesar')
        
        # Procesar cada reserva
        for i, reserva in enumerate(queryset, 1):
            if self.verbose:
                self.stdout.write(f'[{i}/{total_reservas}] Procesando {reserva.codigo_reserva}...')
            
            try:
                resultado = self._procesar_reserva_individual(reserva)
                
                if self.verbose and resultado:
                    self.stdout.write(f'  → {resultado}')
                    
            except Exception as e:
                self.stats['errores'] += 1
                logger.error(f'Error procesando reserva {reserva.codigo_reserva}: {e}')
                
                if self.verbose:
                    self.stdout.write(
                        self.style.ERROR(f'  → ERROR: {str(e)}')
                    )

    def _procesar_reserva_individual(self, reserva):
        """Procesa una reserva individual aplicando las reglas de expiración"""
        
        self.stats['procesadas'] += 1
        now = timezone.now()
        
        # Verificar si ya está pagada
        if reserva.estado == reserva.EstadoChoices.CONFIRMADA:
            self.stats['ya_procesadas'] += 1
            return 'Ya está confirmada y pagada'
        
        # Calcular tiempos
        vuelo_fecha = reserva.vuelo.fecha_salida_estimada
        if not vuelo_fecha:
            return 'Vuelo sin fecha de salida definida'
        
        tiempo_hasta_vuelo = vuelo_fecha - now
        tiempo_hasta_limite = reserva.fecha_limite_pago - now if reserva.fecha_limite_pago else timedelta(0)
        
        # REGLA 1: Menos de 24 horas antes del vuelo - ELIMINAR
        if tiempo_hasta_vuelo <= timedelta(hours=24):
            return self._eliminar_reserva(reserva, 'Menos de 24h antes del vuelo')
        
        # REGLA 2: Pasó el límite de pago (72h antes) - CANCELAR
        elif tiempo_hasta_limite <= timedelta(0):
            return self._cancelar_reserva(reserva, 'Límite de pago expirado')
        
        # REGLA 3: Entre 48h y 72h antes - RECORDATORIO
        elif timedelta(hours=48) <= tiempo_hasta_limite <= timedelta(hours=72):
            return self._enviar_recordatorio(reserva, tiempo_hasta_limite)
        
        # No requiere acción
        else:
            if self.verbose:
                horas_restantes = int(tiempo_hasta_limite.total_seconds() / 3600)
                return f'En espera - {horas_restantes}h para expirar'
            
            return None

    def _eliminar_reserva(self, reserva, motivo):
        """Elimina una reserva expirada"""
        
        if not self.dry_run:
            try:
                with transaction.atomic():
                    codigo = reserva.codigo_reserva  # Guardar antes de eliminar
                    reserva.delete()
                    
                    logger.info(f'Reserva {codigo} eliminada - {motivo}')
                    
            except Exception as e:
                logger.error(f'Error eliminando reserva {reserva.codigo_reserva}: {e}')
                raise
        
        self.stats['eliminadas'] += 1
        return f'ELIMINADA - {motivo}'

    def _cancelar_reserva(self, reserva, motivo):
        """Cancela una reserva por expiración"""
        
        if not self.dry_run:
            try:
                with transaction.atomic():
                    reserva.estado = reserva.EstadoChoices.CANCELADA
                    reserva.activo = False
                    reserva.save(update_fields=['estado', 'activo'])
                    
                    logger.info(f'Reserva {reserva.codigo_reserva} cancelada - {motivo}')
                    
            except Exception as e:
                logger.error(f'Error cancelando reserva {reserva.codigo_reserva}: {e}')
                raise
        
        self.stats['canceladas'] += 1
        
        # Enviar notificación de cancelación
        if self.send_emails:
            try:
                if not self.dry_run:
                    from reservas.utils import enviar_notificacion_reserva
                    if enviar_notificacion_reserva(reserva, 'cancelacion_por_expiracion'):
                        self.stats['notificaciones_cancelacion'] += 1
                else:
                    self.stats['notificaciones_cancelacion'] += 1  # Simular
                    
            except Exception as e:
                logger.error(f'Error enviando notificación de cancelación para {reserva.codigo_reserva}: {e}')
        
        return f'CANCELADA - {motivo}'

    def _enviar_recordatorio(self, reserva, tiempo_restante):
        """Envía recordatorio de pago si corresponde"""
        
        # Verificar si ya se envió recordatorio
        if not self.force_email and reserva.recordatorio_48h_enviado:
            return 'Recordatorio ya enviado previamente'
        
        if self.send_emails:
            try:
                if not self.dry_run:
                    from reservas.utils import enviar_notificacion_reserva
                    
                    if enviar_notificacion_reserva(reserva, 'recordatorio_48h'):
                        # Marcar como enviado
                        reserva.recordatorio_48h_enviado = True
                        reserva.save(update_fields=['recordatorio_48h_enviado'])
                        
                        self.stats['recordatorios_enviados'] += 1
                        
                        horas = int(tiempo_restante.total_seconds() / 3600)
                        return f'RECORDATORIO ENVIADO - {horas}h restantes'
                    else:
                        return 'Error enviando recordatorio'
                else:
                    self.stats['recordatorios_enviados'] += 1  # Simular
                    horas = int(tiempo_restante.total_seconds() / 3600)
                    return f'RECORDATORIO SIMULADO - {horas}h restantes'
                    
            except Exception as e:
                logger.error(f'Error enviando recordatorio para {reserva.codigo_reserva}: {e}')
                return f'Error en recordatorio: {str(e)}'
        else:
            horas = int(tiempo_restante.total_seconds() / 3600)
            return f'Recordatorio pendiente - {horas}h restantes (emails deshabilitados)'

    def _mostrar_reporte_final(self):
        """Muestra el reporte final de la ejecución"""
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📊 REPORTE FINAL DE EJECUCIÓN'))
        self.stdout.write('='*60)
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING('(SIMULACIÓN - No se realizaron cambios reales)'))
        
        # Estadísticas principales
        self.stdout.write(f'📋 Reservas procesadas: {self.stats["procesadas"]}')
        
        if self.stats['eliminadas'] > 0:
            self.stdout.write(
                self.style.ERROR(f'🗑️  Reservas eliminadas (24h): {self.stats["eliminadas"]}')
            )
        
        if self.stats['canceladas'] > 0:
            self.stdout.write(
                self.style.WARNING(f'❌ Reservas canceladas (72h): {self.stats["canceladas"]}')
            )
        
        if self.stats['recordatorios_enviados'] > 0:
            self.stdout.write(
                self.style.HTTP_INFO(f'📧 Recordatorios enviados: {self.stats["recordatorios_enviados"]}')
            )
        
        if self.stats['notificaciones_cancelacion'] > 0:
            self.stdout.write(
                self.style.HTTP_INFO(f'📧 Notificaciones de cancelación: {self.stats["notificaciones_cancelacion"]}')
            )
        
        if self.stats['ya_procesadas'] > 0:
            self.stdout.write(f'✅ Ya procesadas (pagadas): {self.stats["ya_procesadas"]}')
        
        if self.stats['errores'] > 0:
            self.stdout.write(
                self.style.ERROR(f'💥 Errores encontrados: {self.stats["errores"]}')
            )
        
        # Mensaje final
        total_acciones = (
            self.stats['eliminadas'] + 
            self.stats['canceladas'] + 
            self.stats['recordatorios_enviados']
        )
        
        if total_acciones == 0:
            self.stdout.write(self.style.SUCCESS('✨ Todas las reservas están en orden'))
        elif self.stats['errores'] == 0:
            self.stdout.write(self.style.SUCCESS('✅ Procesamiento completado exitosamente'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Procesamiento completado con algunos errores'))
        
        # Información adicional
        self.stdout.write(f'\n⏰ Tiempo de ejecución: {timezone.now().strftime("%H:%M:%S")}')
        
        if not self.send_emails:
            self.stdout.write(
                self.style.HTTP_INFO('💡 Tip: Use --send-emails para enviar notificaciones por email')
            )
        
        if not self.verbose:
            self.stdout.write(
                self.style.HTTP_INFO('💡 Tip: Use --verbose para ver detalles de cada reserva')
            )
        
        self.stdout.write('='*60)
        
        # Log del resumen
        logger.info(
            f'Comando expiración completado - '
            f'Procesadas: {self.stats["procesadas"]}, '
            f'Eliminadas: {self.stats["eliminadas"]}, '
            f'Canceladas: {self.stats["canceladas"]}, '
            f'Recordatorios: {self.stats["recordatorios_enviados"]}, '
            f'Errores: {self.stats["errores"]}'
        )
        


