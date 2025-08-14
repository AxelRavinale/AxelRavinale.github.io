from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, View, TemplateView
)
from django.db import models, transaction
from django.urls import reverse, reverse_lazy
from django.db.models import Q, Count, Sum, Prefetch
from django.http import HttpResponse, JsonResponse, Http404
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.paginator import Paginator
from django.contrib.auth.models import User
import json
import logging
from datetime import timedelta

# Imports de modelos
from .models import (
    Reserva, ReservaDetalle, Boleto, AsientoVuelo, ConfiguracionVuelo
)
from vuelos.models import Vuelo, EscalaVuelo
from aviones.models import Asiento

# Imports de formularios (faltaba SeleccionAsientosForm)
from .forms import (
    ReservaForm, FiltroReservaForm, PagoForm, BusquedaBoletoForm, 
    ConfiguracionAsientoForm, SeleccionAsientosForm  # <- Esta importación faltaba
)

# Import de mixins (si tienes archivo mixins.py separado)
from .mixins import AdminRequiredMixin, UserRequiredMixin  # <- Opcional

# Imports de utils
from .utils import generar_pdf_boleto, generar_pdf_detalle_reserva

logger = logging.getLogger(__name__)


# ================================
# VISTAS PARA ADMINISTRADORES
# ================================

class AdminInicioView(AdminRequiredMixin, LoginRequiredMixin, TemplateView):
    """Vista de inicio para administradores"""
    template_name = 'reservas/admin/inicio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas generales
        context['stats'] = {
            'vuelos_totales': Vuelo.objects.filter(activo=True).count(),
            'vuelos_configurados': ConfiguracionVuelo.objects.filter(configurado=True).count(),
            'vuelos_pendientes': Vuelo.objects.filter(activo=True).exclude(
                configuracion_reserva__configurado=True
            ).count(),
            'reservas_totales': Reserva.objects.filter(activo=True).count(),
            'reservas_pagadas': Reserva.objects.filter(
                activo=True, 
                estado=Reserva.EstadoChoices.CONFIRMADA
            ).count(),
            'ingresos_totales': Reserva.objects.filter(
                activo=True,
                estado=Reserva.EstadoChoices.CONFIRMADA
            ).aggregate(total=Sum('precio_total'))['total'] or 0
        }
        
        # Vuelos recientes que necesitan configuración
        context['vuelos_sin_configurar'] = Vuelo.objects.filter(
            activo=True,
            fecha_salida_estimada__gt=timezone.now()
        ).exclude(
            configuracion_reserva__configurado=True
        ).select_related('origen_principal', 'destino_principal')[:5]
        
        return context


class AdminCrearReservaView(AdminRequiredMixin, LoginRequiredMixin, TemplateView):
    """Vista para que admin inicie el proceso de crear reserva"""
    template_name = 'reservas/admin/crear_reserva.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Vuelos disponibles para configurar (sin configurar aún)
        context['vuelos_sin_configurar'] = Vuelo.objects.filter(
            activo=True,
            fecha_salida_estimada__gt=timezone.now()
        ).exclude(
            configuracion_reserva__configurado=True
        ).select_related('origen_principal', 'destino_principal').order_by('fecha_salida_estimada')
        
        return context


class AdminConfiguracionVueloView(AdminRequiredMixin, LoginRequiredMixin, DetailView):
    """Vista para configurar asientos de un vuelo"""
    model = Vuelo
    template_name = 'reservas/admin/configuracion_vuelo.html'
    context_object_name = 'vuelo'

    def get_object(self):
        vuelo = super().get_object()
        # Crear configuración si no existe
        configuracion, created = ConfiguracionVuelo.objects.get_or_create(vuelo=vuelo)
        return vuelo

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vuelo = self.object
        
        # Obtener o crear configuración
        configuracion, created = ConfiguracionVuelo.objects.get_or_create(vuelo=vuelo)
        context['configuracion'] = configuracion
        
        if vuelo.tiene_escalas:
            # Para vuelos con escalas
            escalas_data = []
            for escala_vuelo in vuelo.escalas_vuelo.filter(activo=True).order_by('orden'):
                asientos_avion = Asiento.objects.filter(
                    avion=escala_vuelo.avion, 
                    activo=True
                ).order_by('fila', 'columna')
                
                asientos_configurados = AsientoVuelo.objects.filter(
                    vuelo=vuelo,
                    escala_vuelo=escala_vuelo,
                    activo=True
                ).select_related('asiento')
                
                escalas_data.append({
                    'escala_vuelo': escala_vuelo,
                    'asientos_avion': asientos_avion,
                    'asientos_configurados': {ac.asiento.id: ac for ac in asientos_configurados},
                    'total_asientos': asientos_avion.count(),
                    'configurados': asientos_configurados.count(),
                    'habilitados': asientos_configurados.filter(habilitado_para_reserva=True).count(),
                })
            
            context['escalas_data'] = escalas_data
        else:
            # Para vuelos directos
            if vuelo.avion_asignado:
                asientos_avion = Asiento.objects.filter(
                    avion=vuelo.avion_asignado, 
                    activo=True
                ).order_by('fila', 'columna')
                
                asientos_configurados = AsientoVuelo.objects.filter(
                    vuelo=vuelo,
                    escala_vuelo__isnull=True,
                    activo=True
                ).select_related('asiento')
                
                context['asientos_avion'] = asientos_avion
                context['asientos_configurados'] = {ac.asiento.id: ac for ac in asientos_configurados}
                context['total_asientos'] = asientos_avion.count()
                context['configurados'] = asientos_configurados.count()
                context['habilitados'] = asientos_configurados.filter(habilitado_para_reserva=True).count()
        
        return context

    def post(self, request, *args, **kwargs):
        vuelo = self.get_object()
        
        try:
            with transaction.atomic():
                configuraciones_realizadas = self._procesar_configuracion_asientos(vuelo, request.POST)
                
                if configuraciones_realizadas > 0:
                    # Marcar vuelo como configurado
                    configuracion, created = ConfiguracionVuelo.objects.get_or_create(vuelo=vuelo)
                    configuracion.marcar_como_configurado(request.user)
                    
                    messages.success(
                        request,
                        _('Configuración guardada exitosamente. {} asientos configurados. '
                          'El vuelo ahora está disponible para reservas de usuarios.').format(configuraciones_realizadas)
                    )
                else:
                    messages.warning(request, _('No se realizaron cambios en la configuración'))
                
                return redirect('reservas:admin_configuracion_vuelo', pk=vuelo.pk)
                
        except Exception as e:
            messages.error(request, _('Error al guardar la configuración: {}').format(str(e)))
            return self.get(request, *args, **kwargs)

    def _procesar_configuracion_asientos(self, vuelo, post_data):
        """Procesa la configuración de asientos desde el POST"""
        configuraciones = 0
        
        for key, value in post_data.items():
            if key.startswith('asiento_'):
                parts = key.split('_')
                if len(parts) >= 3:
                    asiento_id = parts[1]
                    campo = '_'.join(parts[2:])
                    
                    if campo == 'tipo':
                        configuraciones += self._configurar_asiento(
                            vuelo, asiento_id, post_data
                        )
        
        return configuraciones

    def _configurar_asiento(self, vuelo, asiento_id, post_data):
        """Configura un asiento específico"""
        try:
            asiento = Asiento.objects.get(id=asiento_id)
            
            # Determinar escala si existe
            escala_vuelo = None
            if vuelo.tiene_escalas:
                for ev in vuelo.escalas_vuelo.filter(activo=True):
                    if ev.avion == asiento.avion:
                        escala_vuelo = ev
                        break
            
            # Obtener valores del formulario
            tipo = post_data.get(f'asiento_{asiento_id}_tipo', 'ECO')
            precio = post_data.get(f'asiento_{asiento_id}_precio', '0')
            habilitado = post_data.get(f'asiento_{asiento_id}_habilitado') == 'on'
            
            if float(precio) <= 0:
                return 0
            
            # Crear o actualizar configuración
            asiento_vuelo, created = AsientoVuelo.objects.update_or_create(
                vuelo=vuelo,
                asiento=asiento,
                escala_vuelo=escala_vuelo,
                defaults={
                    'tipo_asiento': tipo,
                    'precio': precio,
                    'habilitado_para_reserva': habilitado,
                    'configurado_por': self.request.user,
                    'activo': True
                }
            )
            
            return 1
            
        except (Asiento.DoesNotExist, ValueError, ValidationError):
            return 0


class AdminReservasListView(AdminRequiredMixin, LoginRequiredMixin, ListView):
    """Vista para que admin vea todas las reservas con filtros"""
    model = Reserva
    template_name = 'reservas/admin/reservas_list.html'
    context_object_name = 'reservas'
    paginate_by = 25

    def get_queryset(self):
        queryset = Reserva.objects.filter(activo=True).select_related(
            'pasajero', 'vuelo__origen_principal', 'vuelo__destino_principal'
        ).prefetch_related('detalles__asiento_vuelo__asiento')
        
        # Aplicar filtros
        codigo_reserva = self.request.GET.get('codigo_reserva')
        if codigo_reserva:
            queryset = queryset.filter(codigo_reserva__icontains=codigo_reserva)
        
        vuelo = self.request.GET.get('vuelo')
        if vuelo:
            queryset = queryset.filter(vuelo__codigo_vuelo__icontains=vuelo)
        
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        pasajero = self.request.GET.get('pasajero')
        if pasajero:
            queryset = queryset.filter(
                Q(pasajero__username__icontains=pasajero) |
                Q(pasajero__first_name__icontains=pasajero) |
                Q(pasajero__last_name__icontains=pasajero) |
                Q(pasajero__email__icontains=pasajero)
            )
        
        return queryset.order_by('-fecha_reserva')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Formulario de filtros
        context['filtros'] = {
            'codigo_reserva': self.request.GET.get('codigo_reserva', ''),
            'vuelo': self.request.GET.get('vuelo', ''),
            'estado': self.request.GET.get('estado', ''),
            'pasajero': self.request.GET.get('pasajero', ''),
        }
        
        # Estadísticas
        all_reservas = Reserva.objects.filter(activo=True)
        context['stats'] = {
            'total': all_reservas.count(),
            'sin_pago': all_reservas.filter(estado=Reserva.EstadoChoices.RESERVADO_SIN_PAGO).count(),
            'pagadas': all_reservas.filter(estado=Reserva.EstadoChoices.CONFIRMADA).count(),
            'canceladas': all_reservas.filter(estado=Reserva.EstadoChoices.CANCELADA).count(),
            'ingresos_total': all_reservas.filter(estado=Reserva.EstadoChoices.CONFIRMADA).aggregate(
                total=Sum('precio_total'))['total'] or 0
        }
        
        return context


class AdminReservaDetailView(AdminRequiredMixin, LoginRequiredMixin, DetailView):
    """Vista detallada de reserva para admin"""
    model = Reserva
    template_name = 'reservas/admin/reserva_detail.html'
    context_object_name = 'reserva'

    def get_queryset(self):
        return Reserva.objects.select_related(
            'pasajero', 'vuelo__origen_principal', 'vuelo__destino_principal'
        ).prefetch_related(
            'detalles__asiento_vuelo__asiento__avion',
            'detalles__asiento_vuelo__escala_vuelo'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reserva = self.object
        
        context['puede_pagar'] = not reserva.esta_expirada
        context['horas_limite'] = reserva.horas_para_expiracion
        
        return context

    def post(self, request, *args, **kwargs):
        reserva = self.get_object()
        accion = request.POST.get('accion')
        
        try:
            if accion == 'pagar_ahora':
                return redirect('reservas:procesar_pago', pk=reserva.pk)
            
            elif accion == 'pagar_despues':
                reserva.estado = Reserva.EstadoChoices.RESERVADO_SIN_PAGO
                reserva.save()
                
                messages.success(
                    request,
                    _('Reserva guardada exitosamente. Código: {}. Tienes hasta {} para realizar el pago.').format(
                        reserva.codigo_reserva,
                        reserva.fecha_limite_pago.strftime('%d/%m/%Y %H:%M') if reserva.fecha_limite_pago else 'N/A'
                    )
                )
                
                return redirect('reservas:mis_reservas')
            
            else:
                messages.error(request, _('Acción no válida'))
                
        except ValidationError as e:
            messages.error(request, str(e))
        
        return self.get(request, *args, **kwargs)


class ProcesarPagoView(UserRequiredMixin, LoginRequiredMixin, FormView):
    """Vista para procesar el pago de una reserva"""
    template_name = 'reservas/user/procesar_pago.html'
    form_class = PagoForm

    def get_reserva(self):
        if not hasattr(self, '_reserva'):
            self._reserva = get_object_or_404(
                Reserva,
                pk=self.kwargs['pk'],
                pasajero=self.request.user,
                activo=True
            )
            
            # Verificar que se pueda pagar
            if not self._reserva.puede_pagarse:
                raise Http404(_("Esta reserva no puede ser pagada"))
        
        return self._reserva

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['reserva'] = self.get_reserva()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reserva'] = self.get_reserva()
        return context

    def form_valid(self, form):
        reserva = self.get_reserva()
        
        try:
            with transaction.atomic():
                # Simular procesamiento de pago
                datos_tarjeta = {
                    'numero': form.cleaned_data['numero_tarjeta'],
                    'titular': form.cleaned_data['titular'],
                    'cvv': form.cleaned_data['cvv'],
                    'expiracion': f"{form.cleaned_data['mes_expiracion']}/{form.cleaned_data['año_expiracion']}"
                }
                
                boleto = reserva.procesar_pago(
                    metodo_pago=form.cleaned_data['metodo_pago'],
                    datos_tarjeta=datos_tarjeta
                )
                
                messages.success(
                    self.request,
                    _('¡Pago procesado exitosamente! Su boleto ha sido generado: {}').format(boleto.codigo_barras)
                )
                
                return redirect('reservas:reserva_confirmada', pk=reserva.pk)
                
        except ValidationError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
        except Exception as e:
            form.add_error(None, _('Error al procesar el pago: {}').format(str(e)))
            return self.form_invalid(form)


class ReservaConfirmadaView(UserRequiredMixin, LoginRequiredMixin, DetailView):
    """Vista de confirmación de reserva pagada"""
    model = Reserva
    template_name = 'reservas/user/reserva_confirmada.html'
    context_object_name = 'reserva'

    def get_object(self):
        reserva = get_object_or_404(
            Reserva,
            pk=self.kwargs['pk'],
            pasajero=self.request.user,
            estado=Reserva.EstadoChoices.CONFIRMADA
        )
        return reserva

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['boleto'] = self.object.boleto
        except Boleto.DoesNotExist:
            context['boleto'] = None
        return context


class MisReservasView(UserRequiredMixin, LoginRequiredMixin, ListView):
    """Vista para que usuario vea sus reservas"""
    model = Reserva
    template_name = 'reservas/user/mis_reservas.html'
    context_object_name = 'reservas'
    paginate_by = 10

    def get_queryset(self):
        return Reserva.objects.filter(
            pasajero=self.request.user,
            activo=True
        ).select_related(
            'vuelo__origen_principal',
            'vuelo__destino_principal'
        ).prefetch_related('detalles__asiento_vuelo__asiento').order_by('-fecha_reserva')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas del usuario
        reservas_usuario = self.get_queryset()
        context['stats'] = {
            'total': reservas_usuario.count(),
            'pendientes': reservas_usuario.filter(estado=Reserva.EstadoChoices.RESERVADO_SIN_PAGO).count(),
            'confirmadas': reservas_usuario.filter(estado=Reserva.EstadoChoices.CONFIRMADA).count(),
            'canceladas': reservas_usuario.filter(estado=Reserva.EstadoChoices.CANCELADA).count(),
        }
        
        # Marcar reservas que expiran pronto (48 horas)
        for reserva in context['reservas']:
            if reserva.estado == Reserva.EstadoChoices.RESERVADO_SIN_PAGO and reserva.horas_para_expiracion is not None:
                if reserva.horas_para_expiracion <= 48:
                    reserva.urgente = True
                else:
                    reserva.urgente = False
        
        return context


class ReservaDetailUserView(UserRequiredMixin, LoginRequiredMixin, DetailView):
    """Vista detallada de reserva para usuario"""
    model = Reserva
    template_name = 'reservas/user/reserva_detail.html'
    context_object_name = 'reserva'

    def get_object(self):
        reserva = get_object_or_404(
            Reserva,
            pk=self.kwargs['pk'],
            pasajero=self.request.user,
            activo=True
        )
        return reserva

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reserva = self.object
        
        context['puede_pagar'] = reserva.puede_pagarse
        context['horas_limite'] = reserva.horas_para_expiracion
        
        # Marcar si es urgente (48 horas o menos)
        if reserva.estado == Reserva.EstadoChoices.RESERVADO_SIN_PAGO and reserva.horas_para_expiracion is not None:
            context['urgente'] = reserva.horas_para_expiracion <= 48
        
        # Boleto si existe
        try:
            context['boleto'] = reserva.boleto
        except Boleto.DoesNotExist:
            context['boleto'] = None
        
        return context

    def post(self, request, *args, **kwargs):
        reserva = self.get_object()
        action = request.POST.get('action')
        
        if action == 'pagar_ahora' and reserva.puede_pagarse:
            return redirect('reservas:procesar_pago', pk=reserva.pk)
        
        elif action == 'cancelar' and reserva.estado != Reserva.EstadoChoices.CONFIRMADA:
            try:
                reserva.cancelar()
                messages.success(request, _('Reserva cancelada exitosamente'))
            except ValidationError as e:
                messages.error(request, str(e))
        
        return redirect('reservas:reserva_detail_user', pk=reserva.pk)


# ================================
# VISTAS PARA BOLETOS
# ================================

class BoletoDetailView(LoginRequiredMixin, DetailView):
    """Vista detallada de boleto (accesible por admin y propietario)"""
    model = Boleto
    template_name = 'reservas/boleto_detail.html'
    context_object_name = 'boleto'

    def get_object(self):
        boleto = super().get_object()
        
        # Verificar permisos
        if not self.request.user.is_superuser:
            if boleto.reserva.pasajero != self.request.user:
                raise Http404()
        
        return boleto

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['es_admin'] = self.request.user.is_superuser
        return context


class BuscarBoletoView(TemplateView):
    """Vista para buscar boletos por código de barras (pública)"""
    template_name = 'reservas/buscar_boleto.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = BusquedaBoletoForm()
        return context

    def post(self, request, *args, **kwargs):
        form = BusquedaBoletoForm(request.POST)
        
        if form.is_valid():
            codigo_barras = form.cleaned_data['codigo_barras']
            
            try:
                boleto = Boleto.objects.get(codigo_barras=codigo_barras, activo=True)
                return redirect('reservas:boleto_publico', pk=boleto.pk)
            except Boleto.DoesNotExist:
                messages.error(
                    request,
                    _('No se encontró ningún boleto con el código: {}').format(codigo_barras)
                )
        
        return self.render_to_response(self.get_context_data(form=form))


class BoletoPublicoView(DetailView):
    """Vista pública de boleto (sin login requerido)"""
    model = Boleto
    template_name = 'reservas/boleto_publico.html'
    context_object_name = 'boleto'

    def get_queryset(self):
        return Boleto.objects.filter(activo=True)


class DescargarBoletoView(LoginRequiredMixin, View):
    """Vista para descargar boleto en PDF"""

    def get_boleto(self):
        boleto = get_object_or_404(Boleto, pk=self.kwargs['pk'], activo=True)
        
        # Verificar permisos
        if not self.request.user.is_superuser:
            if boleto.reserva.pasajero != self.request.user:
                raise Http404()
        
        return boleto

    def get(self, request, *args, **kwargs):
        boleto = self.get_boleto()
        
        try:
            pdf_content = generar_pdf_boleto(boleto)
            
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="boleto_{boleto.codigo_barras}.pdf"'
            
            return response
            
        except Exception as e:
            messages.error(request, _('Error al generar PDF: {}').format(str(e)))
            return redirect('reservas:boleto_detail', pk=boleto.pk)


class DescargarDetalleReservaView(LoginRequiredMixin, View):
    """Vista para descargar detalle de reserva (sin pagar)"""

    def get_reserva(self):
        reserva = get_object_or_404(Reserva, pk=self.kwargs['pk'], activo=True)
        
        # Verificar permisos
        if not self.request.user.is_superuser:
            if reserva.pasajero != self.request.user:
                raise Http404()
        
        return reserva

    def get(self, request, *args, **kwargs):
        reserva = self.get_reserva()
        
        try:
            pdf_content = generar_pdf_detalle_reserva(reserva)
            
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="reserva_{reserva.codigo_reserva}.pdf"'
            
            return response
            
        except Exception as e:
            messages.error(request, _('Error al generar PDF: {}').format(str(e)))
            
            if request.user.is_superuser:
                return redirect('reservas:admin_reserva_detail', pk=reserva.pk)
            else:
                return redirect('reservas:reserva_detail_user', pk=reserva.pk)


# ================================
# VISTA DE REDIRECCIÓN
# ================================

class HomeRedirectView(LoginRequiredMixin, View):
    """Vista para redireccionar desde home según tipo de usuario"""

    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return redirect('reservas:admin_inicio')
        else:
            return redirect('reservas:user_inicio')
        
        # Información adicional
        context['puede_modificar'] = reserva.estado != Reserva.EstadoChoices.CANCELADA
        context['puede_validar_pago'] = reserva.estado in [
            Reserva.EstadoChoices.CREADA, 
            Reserva.EstadoChoices.RESERVADO_SIN_PAGO
        ]
        
        # Boleto si existe
        try:
            context['boleto'] = reserva.boleto
        except Boleto.DoesNotExist:
            context['boleto'] = None
        
        return context

    def post(self, request, *args, **kwargs):
        reserva = self.get_object()
        action = request.POST.get('action')
        
        try:
            if action == 'validar_pago':
                boleto = reserva.marcar_pago_manual(request.user)
                messages.success(
                    request, 
                    _('Pago validado exitosamente. Boleto generado: {}').format(boleto.codigo_barras)
                )
            
            elif action == 'cancelar':
                reserva.cancelar()
                messages.success(request, _('Reserva cancelada exitosamente'))
            
            else:
                messages.error(request, _('Acción no válida'))
                
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, _('Error al procesar la acción: {}').format(str(e)))
        
        return redirect('reservas:admin_reserva_detail', pk=reserva.pk)


class AdminVueloReservasView(AdminRequiredMixin, LoginRequiredMixin, DetailView):
    """Vista para ver todas las reservas de un vuelo específico"""
    model = Vuelo
    template_name = 'reservas/admin/vuelo_reservas.html'
    context_object_name = 'vuelo'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vuelo = self.object
        
        # Reservas del vuelo
        reservas = Reserva.objects.filter(
            vuelo=vuelo, 
            activo=True
        ).select_related('pasajero').prefetch_related(
            'detalles__asiento_vuelo__asiento'
        ).order_by('-fecha_reserva')
        
        context['reservas'] = reservas
        
        # Estadísticas del vuelo
        context['stats'] = {
            'total_reservas': reservas.count(),
            'reservas_pagadas': reservas.filter(estado=Reserva.EstadoChoices.CONFIRMADA).count(),
            'reservas_pendientes': reservas.filter(estado=Reserva.EstadoChoices.RESERVADO_SIN_PAGO).count(),
            'ingresos': reservas.filter(estado=Reserva.EstadoChoices.CONFIRMADA).aggregate(
                total=Sum('precio_total'))['total'] or 0,
        }
        
        return context


# ================================
# VISTAS PARA USUARIOS NORMALES
# ================================

class UserInicioView(UserRequiredMixin, LoginRequiredMixin, TemplateView):
    """Vista de inicio para usuarios normales"""
    template_name = 'reservas/user/inicio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas del usuario
        reservas_usuario = Reserva.objects.filter(
            pasajero=self.request.user,
            activo=True
        )
        
        context['stats_usuario'] = {
            'total_reservas': reservas_usuario.count(),
            'reservas_pendientes': reservas_usuario.filter(
                estado=Reserva.EstadoChoices.RESERVADO_SIN_PAGO
            ).count(),
            'reservas_confirmadas': reservas_usuario.filter(
                estado=Reserva.EstadoChoices.CONFIRMADA
            ).count(),
        }
        
        # Reservas recientes del usuario
        context['reservas_recientes'] = reservas_usuario.select_related(
            'vuelo__origen_principal', 'vuelo__destino_principal'
        )[:3]
        
        return context


class VuelosDisponiblesView(UserRequiredMixin, LoginRequiredMixin, ListView):
    """Vista para que usuarios vean vuelos disponibles para reservar"""
    model = Vuelo
    template_name = 'reservas/user/vuelos_disponibles.html'
    context_object_name = 'vuelos'
    paginate_by = 12

    def get_queryset(self):
        # Solo vuelos configurados y con fecha futura
        queryset = Vuelo.objects.filter(
            activo=True,
            fecha_salida_estimada__gt=timezone.now(),
            configuracion_reserva__configurado=True
        ).select_related(
            'origen_principal', 
            'destino_principal', 
            'avion_asignado'
        ).prefetch_related('configuracion_reserva')
        
        # Filtros de búsqueda
        origen = self.request.GET.get('origen')
        if origen:
            queryset = queryset.filter(origen_principal__nombre__icontains=origen)
        
        destino = self.request.GET.get('destino')
        if destino:
            queryset = queryset.filter(destino_principal__nombre__icontains=destino)
        
        fecha = self.request.GET.get('fecha')
        if fecha:
            try:
                from datetime import datetime
                fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_salida_estimada__date=fecha_obj)
            except ValueError:
                pass
        
        return queryset.order_by('fecha_salida_estimada')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Agregar disponibilidad de asientos para cada vuelo
        vuelos_con_disponibilidad = []
        for vuelo in context['vuelos']:
            asientos_totales = AsientoVuelo.objects.filter(
                vuelo=vuelo, 
                activo=True, 
                habilitado_para_reserva=True
            ).count()
            
            asientos_ocupados = ReservaDetalle.objects.filter(
                asiento_vuelo__vuelo=vuelo,
                reserva__activo=True,
                reserva__estado__in=[
                    Reserva.EstadoChoices.CONFIRMADA,
                    Reserva.EstadoChoices.RESERVADO_SIN_PAGO
                ]
            ).count()
            
            disponibles = asientos_totales - asientos_ocupados
            precio_min = AsientoVuelo.objects.filter(
                vuelo=vuelo, 
                activo=True, 
                habilitado_para_reserva=True
            ).aggregate(precio_min=models.Min('precio'))['precio_min'] or 0

            # 📌 Cálculo del porcentaje ocupado
            if asientos_totales > 0:
                porcentaje_ocupado = (asientos_ocupados / asientos_totales) * 100
            else:
                porcentaje_ocupado = 0

            vuelos_con_disponibilidad.append({
                'vuelo': vuelo,
                'asientos_totales': asientos_totales,
                'asientos_ocupados': asientos_ocupados,
                'asientos_disponibles': disponibles,
                'precio_desde': precio_min,
                'porcentaje_ocupado': porcentaje_ocupado  # <- agregado
            })

        
        context['vuelos_con_info'] = vuelos_con_disponibilidad
        
        # Filtros aplicados
        context['filtros'] = {
            'origen': self.request.GET.get('origen', ''),
            'destino': self.request.GET.get('destino', ''),
            'fecha': self.request.GET.get('fecha', ''),
        }
        
        return context




class SeleccionAsientosView(UserRequiredMixin, LoginRequiredMixin, View):
    """Vista simplificada para seleccionar asientos sin mostrar precios"""
    template_name = 'reservas/user/seleccion_asientos.html'

    def get_vuelo(self, pk):
        """Obtener y validar vuelo"""
        vuelo = get_object_or_404(Vuelo, pk=pk)
        
        # Verificar que esté configurado
        try:
            config = vuelo.configuracion_reserva
            if not config.configurado:
                raise Http404(_("Este vuelo no está disponible para reservas"))
        except ConfiguracionVuelo.DoesNotExist:
            raise Http404(_("Este vuelo no está configurado"))

        # Verificar fecha
        if vuelo.fecha_salida_estimada <= timezone.now():
            raise Http404(_("Este vuelo ya no acepta reservas"))

        return vuelo

    def get(self, request, pk):
        """Mostrar formulario de selección"""
        vuelo = self.get_vuelo(pk)
        form = SeleccionAsientosForm(vuelo=vuelo)
        
        context = {
            'vuelo': vuelo,
            'form': form,
            'filtros_aplicados': [],
        }
        
        return render(request, self.template_name, context)

    def post(self, request, pk):
        """Procesar formulario"""
        vuelo = self.get_vuelo(pk)
        accion = request.POST.get('accion', 'filtrar')

        # Crear formulario con datos POST
        form = SeleccionAsientosForm(vuelo=vuelo, data=request.POST)
        
        if accion == 'filtrar':
            # Solo aplicar filtros, no validar selección
            filtros_aplicados = request.POST.getlist('filtro_tipo', [])
            
            context = {
                'vuelo': vuelo,
                'form': form,
                'filtros_aplicados': filtros_aplicados,
            }
            
            return render(request, self.template_name, context)
        
        elif accion == 'continuar':
            # Solo validar que haya seleccionado asientos
            if form.is_valid():
                selected_ids = form.cleaned_data['asientos_seleccionados']
                
                if not selected_ids:
                    messages.error(request, _('Debe seleccionar al menos un asiento'))
                    filtros_aplicados = request.POST.getlist('filtro_tipo', [])
                    context = {
                        'vuelo': vuelo,
                        'form': form,
                        'filtros_aplicados': filtros_aplicados,
                    }
                    return render(request, self.template_name, context)
                
                # Guardar selección en sesión y redirigir a confirmación
                request.session['asientos_seleccionados'] = selected_ids
                request.session['vuelo_id'] = vuelo.pk
                
                messages.success(
                    request, 
                    f"✅ Asientos seleccionados exitosamente. "
                    f"Cantidad: {len(selected_ids)}"
                )
                
                # Redirigir a página de confirmación con cálculo de precios
                return redirect('reservas:confirmar_seleccion', pk=vuelo.pk)
            
            else:
                # Mostrar errores del formulario
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, error)
                
                # Si hay errores, mantener filtros aplicados
                filtros_aplicados = request.POST.getlist('filtro_tipo', [])
                context = {
                    'vuelo': vuelo,
                    'form': form,
                    'filtros_aplicados': filtros_aplicados,
                }
                return render(request, self.template_name, context)
        
        # Acción no válida
        messages.error(request, _('Acción no válida'))
        return redirect('reservas:seleccion_asientos', pk=pk)


class ConfirmarSeleccionView(UserRequiredMixin, LoginRequiredMixin, View):
    """Vista para confirmar selección y mostrar precios antes de crear reserva"""
    template_name = 'reservas/user/confirmar_seleccion.html'

    def get(self, request, pk):
        """Mostrar resumen de selección con precios"""
        # Verificar que haya selección en sesión
        asientos_ids = request.session.get('asientos_seleccionados')
        vuelo_id_session = request.session.get('vuelo_id')
        
        if not asientos_ids or vuelo_id_session != pk:
            messages.error(request, _('No hay asientos seleccionados. Seleccione asientos primero.'))
            return redirect('reservas:seleccion_asientos', pk=pk)
        
        vuelo = get_object_or_404(Vuelo, pk=pk)
        
        # Obtener detalles de asientos seleccionados
        asientos_seleccionados = []
        precio_total = 0
        
        for asiento_id in asientos_ids:
            try:
                asiento_vuelo = AsientoVuelo.objects.select_related('asiento').get(
                    id=asiento_id,
                    vuelo=vuelo
                )
                
                # Verificar que siga disponible
                if not ReservaDetalle.objects.filter(
                    asiento_vuelo=asiento_vuelo,
                    reserva__activo=True,
                    reserva__estado__in=['CRE', 'CON', 'RSP']
                ).exists():
                    asientos_seleccionados.append({
                        'asiento_vuelo': asiento_vuelo,
                        'numero': asiento_vuelo.asiento.numero,
                        'tipo': asiento_vuelo.asiento.get_tipo_display(),
                        'precio': asiento_vuelo.precio,
                    })
                    precio_total += asiento_vuelo.precio
                else:
                    # Asiento ya no disponible
                    messages.warning(
                        request, 
                        f'El asiento {asiento_vuelo.asiento.numero} ya no está disponible.'
                    )
                    
            except AsientoVuelo.DoesNotExist:
                messages.warning(request, 'Algunos asientos seleccionados ya no existen.')
        
        if not asientos_seleccionados:
            messages.error(request, _('Los asientos seleccionados ya no están disponibles.'))
            # Limpiar sesión
            if 'asientos_seleccionados' in request.session:
                del request.session['asientos_seleccionados']
            if 'vuelo_id' in request.session:
                del request.session['vuelo_id']
            return redirect('reservas:seleccion_asientos', pk=pk)
        
        context = {
            'vuelo': vuelo,
            'asientos_seleccionados': asientos_seleccionados,
            'precio_total': precio_total,
            'cantidad_asientos': len(asientos_seleccionados),
        }
        
        return render(request, self.template_name, context)

    def post(self, request, pk):
        """Crear la reserva definitiva"""
        # Verificar sesión
        asientos_ids = request.session.get('asientos_seleccionados')
        vuelo_id_session = request.session.get('vuelo_id')
        
        if not asientos_ids or vuelo_id_session != pk:
            messages.error(request, _('Sesión expirada. Seleccione asientos nuevamente.'))
            return redirect('reservas:seleccion_asientos', pk=pk)
        
        vuelo = get_object_or_404(Vuelo, pk=pk)
        
        try:
            with transaction.atomic():
                # Verificar que no tenga reserva activa para este vuelo
                reserva_existente = Reserva.objects.filter(
                    pasajero=request.user,
                    vuelo=vuelo,
                    activo=True,
                    estado__in=['CRE', 'CON', 'RSP']
                ).first()
                
                if reserva_existente:
                    raise ValidationError(_('Ya tiene una reserva activa para este vuelo'))
                
                # Crear reserva
                reserva = Reserva.objects.create(
                    pasajero=request.user,
                    vuelo=vuelo,
                    estado='CRE'
                )
                
                # Agregar detalles de asientos
                asientos_agregados = []
                precio_total = 0
                
                for asiento_id in asientos_ids:
                    try:
                        asiento_vuelo = AsientoVuelo.objects.select_for_update().get(
                            id=asiento_id,
                            vuelo=vuelo
                        )
                        
                        # Verificar disponibilidad nuevamente
                        if ReservaDetalle.objects.filter(
                            asiento_vuelo=asiento_vuelo,
                            reserva__activo=True,
                            reserva__estado__in=['CRE', 'CON', 'RSP']
                        ).exists():
                            raise ValidationError(
                                f"El asiento {asiento_vuelo.asiento.numero} ya no está disponible"
                            )
                        
                        ReservaDetalle.objects.create(
                            reserva=reserva,
                            asiento_vuelo=asiento_vuelo,
                            precio_pagado=asiento_vuelo.precio
                        )
                        
                        asientos_agregados.append(asiento_vuelo.asiento.numero)
                        precio_total += asiento_vuelo.precio
                        
                    except AsientoVuelo.DoesNotExist:
                        raise ValidationError("Un asiento seleccionado ya no existe")
                
                if not asientos_agregados:
                    raise ValidationError("No se pudieron reservar los asientos seleccionados")
                
                # Guardar precio total
                reserva.precio_total = precio_total
                reserva.save()
                
                # Limpiar sesión
                if 'asientos_seleccionados' in request.session:
                    del request.session['asientos_seleccionados']
                if 'vuelo_id' in request.session:
                    del request.session['vuelo_id']
                
                messages.success(
                    request,
                    f"✅ Reserva creada exitosamente. "
                    f"Asientos: {', '.join(asientos_agregados)}. "
                    f"Total: ${precio_total:.2f}"
                )
                
                # Redirigir a detalles de la reserva
                return redirect('reservas:reserva_detail', pk=reserva.pk)
                
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('reservas:seleccion_asientos', pk=pk)
        except Exception as e:
            messages.error(request, f'Error inesperado: {str(e)}')
            return redirect('reservas:seleccion_asientos', pk=pk)


class ConfirmarReservaView(UserRequiredMixin, LoginRequiredMixin, View):
    """Vista mejorada para confirmar reserva"""
    
    template_name = 'reservas/user/confirmar_reserva.html'
    
    def get(self, request, pk):
        """Muestra la página de confirmación"""
        reserva = self._get_reserva(request, pk)
        
        context = {
            'reserva': reserva,
            'puede_pagar': reserva.puede_pagarse,
            'horas_limite': reserva.horas_para_expiracion,
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request, pk):
        """Procesa la confirmación de reserva"""
        reserva = self._get_reserva(request, pk)
        accion = request.POST.get('accion')
        
        try:
            if accion == 'pagar_ahora':
                return redirect('reservas:procesar_pago', pk=reserva.pk)
            
            elif accion == 'pagar_despues':
                # Cambiar estado a reservado sin pago
                reserva.estado = Reserva.EstadoChoices.RESERVADO_SIN_PAGO
                reserva.save()
                
                messages.success(
                    request,
                    f'✅ Reserva guardada exitosamente. '
                    f'Código: {reserva.codigo_reserva}. '
                    f'Tienes hasta {reserva.fecha_limite_pago.strftime("%d/%m/%Y %H:%M") if reserva.fecha_limite_pago else "N/A"} '
                    f'para realizar el pago.'
                )
                return redirect('reservas:mis_reservas')
            
            elif accion == 'cancelar':
                reserva.cancelar()
                messages.success(request, _('Reserva cancelada exitosamente'))
                return redirect('reservas:vuelos_disponibles')
            
            else:
                messages.error(request, _('Acción no válida'))
                
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.error(f"Error en ConfirmarReservaView: {str(e)}")
            messages.error(request, f'⚠️ Error al procesar la confirmación: {str(e)}')
        
        return redirect('reservas:confirmar_reserva', pk=reserva.pk)
    
    def _get_reserva(self, request, pk):
        """Helper para obtener reserva del usuario"""
        return get_object_or_404(
            Reserva.objects.select_related('vuelo', 'pasajero').prefetch_related(
                'detalles__asiento_vuelo__asiento',
                'detalles__asiento_vuelo__escala_vuelo'
            ),
            pk=pk,
            pasajero=request.user,
            activo=True
        )

    def _get_asientos_info(self, reserva):
        """Helper para obtener información de asientos"""
        return [{
            'asiento': detalle.asiento_vuelo.asiento,
            'tipo': detalle.asiento_vuelo.get_tipo_asiento_display(),
            'precio': detalle.precio_pagado,
        } for detalle in reserva.detalles.select_related('asiento_vuelo__asiento')]