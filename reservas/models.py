import uuid
import secrets
import string
from datetime import timedelta
from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse
import json

from aviones.models import Asiento, Avion
from vuelos.models import Vuelo, EscalaVuelo


class AsientoVuelo(models.Model):
    """
    Configuración de asientos por vuelo establecida por el admin.
    Solo después de esta configuración los usuarios pueden hacer reservas.
    """
    vuelo = models.ForeignKey(
        Vuelo,
        on_delete=models.CASCADE,
        related_name='asientos_configurados',
        verbose_name=_("Vuelo")
    )
    
    escala_vuelo = models.ForeignKey(
        EscalaVuelo,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name=_("Escala de Vuelo"),
        help_text=_("Solo para vuelos con escalas")
    )
    
    asiento = models.ForeignKey(
        Asiento,
        on_delete=models.CASCADE,
        verbose_name=_("Asiento")
    )
    
    class TipoAsientoChoices(models.TextChoices):
        ECONOMICO = 'ECO', _('Económico')
        PREMIUM = 'PRE', _('Premium')
        EJECUTIVO = 'EJE', _('Ejecutivo')
        PRIMERA_CLASE = 'PRI', _('Primera Clase')
    
    tipo_asiento = models.CharField(
        max_length=3,
        choices=TipoAsientoChoices.choices,
        default=TipoAsientoChoices.ECONOMICO,
        verbose_name=_("Tipo de Asiento")
    )
    
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Precio")
    )
    
    habilitado_para_reserva = models.BooleanField(
        default=True,
        verbose_name=_("Habilitado para Reserva")
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name=_("Activo")
    )
    
    fecha_configuracion = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Fecha de Configuración")
    )
    
    configurado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Configurado Por")
    )

    class Meta:
        verbose_name = _("Asiento de Vuelo")
        verbose_name_plural = _("Asientos de Vuelo")
        unique_together = ('vuelo', 'asiento', 'escala_vuelo')
        ordering = ['vuelo', 'escala_vuelo__orden', 'asiento__fila', 'asiento__columna']

    def __str__(self):
        if self.escala_vuelo:
            return f"{self.asiento.numero} - {self.get_tipo_asiento_display()} - Escala {self.escala_vuelo.orden} - {self.vuelo.codigo_vuelo}"
        return f"{self.asiento.numero} - {self.get_tipo_asiento_display()} - {self.vuelo.codigo_vuelo}"

    def clean(self):
        # Validar que el asiento pertenece al avión correcto
        if self.escala_vuelo:
            if self.asiento.avion != self.escala_vuelo.avion:
                raise ValidationError(
                    f"El asiento {self.asiento.numero} no pertenece al avión de la escala {self.escala_vuelo.orden}"
                )
        else:
            if self.vuelo.avion_asignado and self.asiento.avion != self.vuelo.avion_asignado:
                raise ValidationError(
                    f"El asiento {self.asiento.numero} no pertenece al avión del vuelo"
                )
            elif not self.vuelo.avion_asignado and not self.vuelo.tiene_escalas:
                raise ValidationError("El vuelo debe tener un avión asignado o escalas configuradas")
        
        # El precio debe ser positivo
        if self.precio and self.precio <= 0:
            raise ValidationError(_("El precio debe ser mayor a 0"))

    @property
    def esta_reservado(self):
        """Verifica si este asiento está reservado por alguna reserva activa"""
        return ReservaDetalle.objects.filter(
            asiento_vuelo=self,
            reserva__activo=True,
            reserva__estado__in=[
                Reserva.EstadoChoices.CREADA,
                Reserva.EstadoChoices.CONFIRMADA,
                Reserva.EstadoChoices.RESERVADO_SIN_PAGO
            ]
        ).exists()


class Reserva(models.Model):
    """Modelo principal de reservas"""
    
    pasajero = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reservas',
        verbose_name=_("Pasajero")
    )
    
    vuelo = models.ForeignKey(
        Vuelo,
        on_delete=models.CASCADE,
        related_name='reservas',
        verbose_name=_("Vuelo")
    )
    
    fecha_reserva = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Fecha de Reserva")
    )
    
    codigo_reserva = models.CharField(
        max_length=16,
        unique=True,
        editable=False,
        verbose_name=_("Código de Reserva")
    )
    
    class EstadoChoices(models.TextChoices):
        CREADA = 'CRE', _('Creada')
        RESERVADO_SIN_PAGO = 'RSP', _('Reservado Sin Pago')
        CONFIRMADA = 'CON', _('Confirmada y Pagada')
        CANCELADA = 'CAN', _('Cancelada')
        EXPIRADA = 'EXP', _('Expirada')
    
    estado = models.CharField(
        max_length=3,
        choices=EstadoChoices.choices,
        default=EstadoChoices.CREADA,
        verbose_name=_("Estado")
    )
    
    precio_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Precio Total")
    )
    
    # Control de pagos y tiempos
    fecha_limite_pago = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Fecha Límite de Pago")
    )
    
    fecha_pago = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Fecha de Pago")
    )
    
    metodo_pago = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Método de Pago")
    )
    
    # Datos de tarjeta (ficticios)
    numero_tarjeta_enmascarado = models.CharField(
        max_length=19,
        blank=True,
        verbose_name=_("Número de Tarjeta (enmascarado)")
    )
    
    # Control de estado
    activo = models.BooleanField(
        default=True,
        verbose_name=_("Activo")
    )
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Reserva")
        verbose_name_plural = _("Reservas")
        ordering = ['-fecha_reserva']
        indexes = [
            models.Index(fields=['codigo_reserva']),
            models.Index(fields=['pasajero', 'estado']),
            models.Index(fields=['vuelo', 'estado']),
            models.Index(fields=['fecha_limite_pago']),
        ]

    def __str__(self):
        return f"Reserva {self.codigo_reserva} - {self.pasajero.get_full_name()} - {self.vuelo.codigo_vuelo}"

    def save(self, *args, **kwargs):
        # Generar código de reserva único
        if not self.codigo_reserva:
            self.codigo_reserva = self._generar_codigo_reserva()
        
        # Establecer fecha límite de pago (72h antes del vuelo)
        if not self.fecha_limite_pago and self.vuelo.fecha_salida_estimada:
            self.fecha_limite_pago = self.vuelo.fecha_salida_estimada - timedelta(hours=72)
        
        super().save(*args, **kwargs)

    def _generar_codigo_reserva(self):
        """Genera un código de reserva único de 8 caracteres"""
        while True:
            codigo = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            if not Reserva.objects.filter(codigo_reserva=codigo).exists():
                return codigo

    @transaction.atomic
    def calcular_precio_total(self):
        """Calcula el precio total sumando todos los asientos reservados"""
        total = self.detalles.aggregate(
            total=models.Sum('precio_pagado')
        )['total'] or 0
        self.precio_total = total
        self.save(update_fields=['precio_total'])
        return total

    @transaction.atomic
    def procesar_pago(self, metodo_pago, datos_tarjeta=None):
        """Procesa el pago de la reserva y genera el boleto"""
        if self.estado == self.EstadoChoices.CONFIRMADA:
            raise ValidationError(_("Esta reserva ya está pagada"))
        
        if self.esta_expirada:
            raise ValidationError(_("Esta reserva ha expirado"))
        
        # Actualizar datos de pago
        self.estado = self.EstadoChoices.CONFIRMADA
        self.fecha_pago = timezone.now()
        self.metodo_pago = metodo_pago
        
        # Enmascarar número de tarjeta si se proporciona
        if datos_tarjeta and datos_tarjeta.get('numero'):
            numero = datos_tarjeta['numero']
            self.numero_tarjeta_enmascarado = f"****-****-****-{numero[-4:]}"
        
        self.save()
        
        # Generar boleto
        boleto = Boleto.objects.create(reserva=self)
        return boleto

    @transaction.atomic
    def marcar_pago_manual(self, usuario_admin):
        """Permite al admin marcar manualmente una reserva como pagada"""
        if not usuario_admin.is_superuser:
            raise ValidationError(_("Solo los administradores pueden marcar pagos manualmente"))
        
        self.estado = self.EstadoChoices.CONFIRMADA
        self.fecha_pago = timezone.now()
        self.metodo_pago = "Validación manual por admin"
        self.save()
        
        # Generar boleto
        boleto = Boleto.objects.create(reserva=self)
        return boleto

    @transaction.atomic
    def cancelar(self, motivo=""):
        """Cancela la reserva"""
        if self.estado == self.EstadoChoices.CONFIRMADA:
            raise ValidationError(_("No se puede cancelar una reserva ya pagada"))
        
        self.estado = self.EstadoChoices.CANCELADA
        self.activo = False
        self.save()

    @property
    def esta_expirada(self):
        """Verifica si la reserva ha expirado"""
        if self.estado == self.EstadoChoices.CONFIRMADA:
            return False
        
        if not self.fecha_limite_pago:
            return False
            
        return timezone.now() > self.fecha_limite_pago

    @property
    def horas_para_expiracion(self):
        """Calcula las horas restantes para la expiración"""
        if self.estado == self.EstadoChoices.CONFIRMADA or not self.fecha_limite_pago:
            return None
            
        delta = self.fecha_limite_pago - timezone.now()
        if delta.total_seconds() <= 0:
            return 0
        return int(delta.total_seconds() / 3600)

    @property
    def puede_pagarse(self):
        """Verifica si la reserva puede ser pagada"""
        return (self.estado in [self.EstadoChoices.CREADA, self.EstadoChoices.RESERVADO_SIN_PAGO] 
                and not self.esta_expirada)

    def get_absolute_url(self):
        return reverse('reservas:reserva_detail_user', kwargs={'pk': self.pk})


class ReservaDetalle(models.Model):
    """Detalles de asientos reservados"""
    
    reserva = models.ForeignKey(
        Reserva,
        related_name='detalles',
        on_delete=models.CASCADE,
        verbose_name=_("Reserva")
    )
    
    asiento_vuelo = models.ForeignKey(
        AsientoVuelo,
        on_delete=models.PROTECT,
        verbose_name=_("Asiento de Vuelo")
    )
    
    precio_pagado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Precio Pagado"),
        help_text=_("Precio al momento de la reserva")
    )
    
    fecha_asignacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Fecha de Asignación")
    )

    class Meta:
        verbose_name = _("Detalle de Reserva")
        verbose_name_plural = _("Detalles de Reserva")
        unique_together = ('reserva', 'asiento_vuelo')

    def __str__(self):
        return f"{self.asiento_vuelo.asiento.numero} - {self.reserva.codigo_reserva}"

    def clean(self):
        # Verificar que el asiento esté disponible
        if self.asiento_vuelo.esta_reservado:
            existing_reserva = ReservaDetalle.objects.filter(
                asiento_vuelo=self.asiento_vuelo,
                reserva__activo=True,
                reserva__estado__in=[
                    Reserva.EstadoChoices.CREADA,
                    Reserva.EstadoChoices.CONFIRMADA,
                    Reserva.EstadoChoices.RESERVADO_SIN_PAGO
                ]
            ).exclude(pk=self.pk).first()
            
            if existing_reserva:
                raise ValidationError(
                    f"El asiento {self.asiento_vuelo.asiento.numero} ya está reservado por {existing_reserva.reserva.codigo_reserva}"
                )
        
        # Verificar que el asiento esté habilitado para reserva
        if not self.asiento_vuelo.habilitado_para_reserva:
            raise ValidationError(f"El asiento {self.asiento_vuelo.asiento.numero} no está habilitado para reservas")
        
        # El precio debe ser positivo
        if self.precio_pagado and self.precio_pagado <= 0:
            raise ValidationError(_("El precio debe ser mayor a 0"))

    def save(self, *args, **kwargs):
        # Establecer precio si no se ha establecido
        if not self.precio_pagado:
            self.precio_pagado = self.asiento_vuelo.precio
        
        self.full_clean()
        super().save(*args, **kwargs)
        
        # Actualizar precio total de la reserva
        self.reserva.calcular_precio_total()

    def delete(self, *args, **kwargs):
        reserva = self.reserva
        super().delete(*args, **kwargs)
        reserva.calcular_precio_total()

    @property
    def asiento(self):
        return self.asiento_vuelo.asiento
    
    @property
    def escala_vuelo(self):
        return self.asiento_vuelo.escala_vuelo


class Boleto(models.Model):
    """Boletos generados tras el pago"""
    
    reserva = models.OneToOneField(
        Reserva,
        related_name='boleto',
        on_delete=models.CASCADE,
        verbose_name=_("Reserva")
    )
    
    codigo_barras = models.CharField(
        max_length=16,
        unique=True,
        editable=False,
        verbose_name=_("Código de Barras")
    )
    
    fecha_emision = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Fecha de Emisión")
    )
    
    # Snapshots para preservar información al momento de la emisión
    vuelo_snapshot = models.TextField(
        verbose_name=_("Datos del Vuelo"),
        help_text=_("JSON con información del vuelo al momento de emisión")
    )
    
    asientos_snapshot = models.TextField(
        verbose_name=_("Datos de Asientos"),
        help_text=_("JSON con información de asientos al momento de emisión")
    )
    
    pasajero_snapshot = models.TextField(
        verbose_name=_("Datos del Pasajero"),
        help_text=_("JSON con información del pasajero al momento de emisión")
    )
    
    # Control de uso
    usado = models.BooleanField(
        default=False,
        verbose_name=_("Usado")
    )
    
    fecha_uso = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Fecha de Uso")
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name=_("Activo")
    )

    class Meta:
        verbose_name = _("Boleto")
        verbose_name_plural = _("Boletos")
        ordering = ['-fecha_emision']
        indexes = [
            models.Index(fields=['codigo_barras']),
            models.Index(fields=['reserva']),
        ]

    def __str__(self):
        return f"Boleto {self.codigo_barras} - {self.reserva.codigo_reserva}"

    def save(self, *args, **kwargs):
        # Generar código de barras único
        if not self.codigo_barras:
            self.codigo_barras = self._generar_codigo_barras()
        
        # Generar snapshots al crear
        if not self.pk:
            self.vuelo_snapshot = self._generar_vuelo_snapshot()
            self.asientos_snapshot = self._generar_asientos_snapshot()
            self.pasajero_snapshot = self._generar_pasajero_snapshot()
        
        super().save(*args, **kwargs)

    def _generar_codigo_barras(self):
        """Genera un código de barras único"""
        while True:
            codigo = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12))
            if not Boleto.objects.filter(codigo_barras=codigo).exists():
                return codigo

    def _generar_vuelo_snapshot(self):
        """Genera snapshot con datos del vuelo"""
        vuelo = self.reserva.vuelo
        data = {
            'codigo_vuelo': vuelo.codigo_vuelo,
            'origen': vuelo.origen_principal.nombre if vuelo.origen_principal else None,
            'destino': vuelo.destino_principal.nombre if vuelo.destino_principal else None,
            'fecha_salida': vuelo.fecha_salida_estimada.isoformat() if vuelo.fecha_salida_estimada else None,
            'fecha_llegada': vuelo.fecha_llegada_estimada.isoformat() if vuelo.fecha_llegada_estimada else None,
            'tiene_escalas': vuelo.tiene_escalas,
            'avion_principal': vuelo.avion_asignado.modelo if vuelo.avion_asignado else None,
        }
        
        if vuelo.tiene_escalas:
            escalas = []
            for escala_vuelo in vuelo.escalas_vuelo.filter(activo=True).order_by('orden'):
                escalas.append({
                    'orden': escala_vuelo.orden,
                    'origen': escala_vuelo.origen.nombre,
                    'destino': escala_vuelo.destino.nombre,
                    'fecha_salida': escala_vuelo.fecha_salida.isoformat(),
                    'fecha_llegada': escala_vuelo.fecha_llegada.isoformat(),
                    'avion': escala_vuelo.avion.modelo,
                })
            data['escalas'] = escalas
        
        return json.dumps(data, ensure_ascii=False)

    def _generar_asientos_snapshot(self):
        """Genera snapshot con datos de asientos"""
        asientos = []
        for detalle in self.reserva.detalles.all():
            asiento_data = {
                'numero': detalle.asiento.numero,
                'fila': detalle.asiento.fila,
                'columna': detalle.asiento.columna,
                'tipo': detalle.asiento_vuelo.get_tipo_asiento_display(),
                'precio': str(detalle.precio_pagado),
                'avion': detalle.asiento.avion.modelo,
            }
            
            if detalle.escala_vuelo:
                asiento_data['escala'] = {
                    'orden': detalle.escala_vuelo.orden,
                    'origen': detalle.escala_vuelo.origen.nombre,
                    'destino': detalle.escala_vuelo.destino.nombre,
                }
            
            asientos.append(asiento_data)
        
        return json.dumps(asientos, ensure_ascii=False)

    def _generar_pasajero_snapshot(self):
        """Genera snapshot con datos del pasajero"""
        pasajero = self.reserva.pasajero
        data = {
            'username': pasajero.username,
            'first_name': pasajero.first_name,
            'last_name': pasajero.last_name,
            'email': pasajero.email,
            'full_name': pasajero.get_full_name(),
        }
        return json.dumps(data, ensure_ascii=False)

    @property
    def vuelo_data(self):
        """Retorna datos del vuelo parseados"""
        return json.loads(self.vuelo_snapshot) if self.vuelo_snapshot else {}

    @property
    def asientos_data(self):
        """Retorna datos de asientos parseados"""
        return json.loads(self.asientos_snapshot) if self.asientos_snapshot else []

    @property
    def pasajero_data(self):
        """Retorna datos del pasajero parseados"""
        return json.loads(self.pasajero_snapshot) if self.pasajero_snapshot else {}

    def get_absolute_url(self):
        return reverse('reservas:boleto_detail', kwargs={'pk': self.pk})

    @transaction.atomic
    def marcar_como_usado(self):
        """Marca el boleto como usado"""
        self.usado = True
        self.fecha_uso = timezone.now()
        self.save(update_fields=['usado', 'fecha_uso'])


class ConfiguracionVuelo(models.Model):
    """
    Modelo para controlar si un vuelo ya fue configurado por el admin.
    Solo después de la configuración los usuarios pueden ver el vuelo.
    """
    vuelo = models.OneToOneField(
        Vuelo,
        on_delete=models.CASCADE,
        related_name='configuracion_reserva',
        verbose_name=_("Vuelo")
    )
    
    configurado = models.BooleanField(
        default=False,
        verbose_name=_("Configurado")
    )
    
    fecha_configuracion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Fecha de Configuración")
    )
    
    configurado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Configurado Por")
    )
    
    total_asientos_configurados = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total Asientos Configurados")
    )
    
    asientos_habilitados = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Asientos Habilitados")
    )

    class Meta:
        verbose_name = _("Configuración de Vuelo")
        verbose_name_plural = _("Configuraciones de Vuelo")

    def __str__(self):
        estado = "Configurado" if self.configurado else "Pendiente"
        return f"{self.vuelo.codigo_vuelo} - {estado}"

    @transaction.atomic
    def marcar_como_configurado(self, usuario):
        """Marca el vuelo como configurado"""
        self.configurado = True
        self.fecha_configuracion = timezone.now()
        self.configurado_por = usuario
        self.actualizar_contadores()
        self.save()

    def actualizar_contadores(self):
        """Actualiza los contadores de asientos"""
        asientos_vuelo = AsientoVuelo.objects.filter(vuelo=self.vuelo, activo=True)
        self.total_asientos_configurados = asientos_vuelo.count()
        self.asientos_habilitados = asientos_vuelo.filter(habilitado_para_reserva=True).count()