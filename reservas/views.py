from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, View, TemplateView
)
from django.urls import reverse, reverse_lazy
from django.db import transaction
from django.db.models import Q, Count, Sum, Prefetch
from django.http import HttpResponse, JsonResponse, Http404
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.paginator import Paginator
import json
from datetime import timedelta

from .models import (
    Reserva, ReservaDetalle, Boleto, AsientoVuelo, ConfiguracionVuelo
)
from .forms import (
    ReservaForm, FiltroReservaForm, PagoForm, BusquedaBoletoForm, 
    ConfiguracionAsientoForm
)
from vuelos.models import Vuelo, EscalaVuelo
from aviones.models import Asiento
from .utils import generar_pdf_boleto, generar_pdf_detalle_reserva
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

# ================================
# MIXINS DE PERMISOS
# ================================

class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin que requiere permisos de administrador"""
    def test_func(self):
        return self.request.user.is_superuser
    
    def handle_no_permission(self):
        messages.error(self.request, _("No tienes permisos para acceder a esta sección"))
        return redirect('home')


class UserRequiredMixin(UserPassesTestMixin):
    """Mixin que requiere que NO sea admin (usuarios normales)"""
    def test_func(self):
        return self.request.user.is_authenticated and not self.request.user.is_superuser
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('login')
        messages.error(self.request, _("Esta sección es solo para usuarios"))
        return redirect('home')


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
            
            vuelos_con_disponibilidad.append({
                'vuelo': vuelo,
                'asientos_totales': asientos_totales,
                'asientos_ocupados': asientos_ocupados,
                'asientos_disponibles': disponibles,
                'precio_desde': precio_min
            })
        
        context['vuelos_con_info'] = vuelos_con_disponibilidad
        
        # Filtros aplicados
        context['filtros'] = {
            'origen': self.request.GET.get('origen', ''),
            'destino': self.request.GET.get('destino', ''),
            'fecha': self.request.GET.get('fecha', ''),
        }
        
        return context


class SeleccionAsientosView(UserRequiredMixin, LoginRequiredMixin, DetailView):
    """Vista para seleccionar asientos de un vuelo"""
    model = Vuelo
    template_name = 'reservas/user/seleccion_asientos.html'
    context_object_name = 'vuelo'

    def get_object(self):
        vuelo = super().get_object()
        
        # Verificar que el vuelo esté configurado y disponible
        try:
            config = vuelo.configuracion_reserva
            if not config.configurado:
                raise Http404(_("Este vuelo no está disponible para reservas"))
        except ConfiguracionVuelo.DoesNotExist:
            raise Http404(_("Este vuelo no está configurado"))
        
        # Verificar que no sea muy tarde para reservar
        if vuelo.fecha_salida_estimada <= timezone.now():
            raise Http404(_("Este vuelo ya no acepta reservas"))
        
        return vuelo

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vuelo = self.object
        
        # Obtener asientos configurados
        if vuelo.tiene_escalas:
            # Para vuelos con escalas
            escalas_data = []
            for escala_vuelo in vuelo.escalas_vuelo.filter(activo=True).order_by('orden'):
                asientos_configurados = AsientoVuelo.objects.filter(
                    vuelo=vuelo,
                    escala_vuelo=escala_vuelo,
                    activo=True,
                    habilitado_para_reserva=True
                ).select_related('asiento').order_by('asiento__fila', 'asiento__columna')
                
                # Marcar asientos ocupados
                asientos_ocupados = set(
                    ReservaDetalle.objects.filter(
                        asiento_vuelo__vuelo=vuelo,
                        asiento_vuelo__escala_vuelo=escala_vuelo,
                        reserva__activo=True,
                        reserva__estado__in=[
                            Reserva.EstadoChoices.CONFIRMADA,
                            Reserva.EstadoChoices.RESERVADO_SIN_PAGO
                        ]
                    ).values_list('asiento_vuelo__asiento__id', flat=True)
                )
                
                escalas_data.append({
                    'escala_vuelo': escala_vuelo,
                    'asientos': asientos_configurados,
                    'asientos_ocupados': asientos_ocupados
                })
            
            context['escalas_data'] = escalas_data
        else:
            # Para vuelos directos
            asientos_configurados = AsientoVuelo.objects.filter(
                vuelo=vuelo,
                escala_vuelo__isnull=True,
                activo=True,
                habilitado_para_reserva=True
            ).select_related('asiento').order_by('asiento__fila', 'asiento__columna')
            
            # Marcar asientos ocupados
            asientos_ocupados = set(
                ReservaDetalle.objects.filter(
                    asiento_vuelo__vuelo=vuelo,
                    asiento_vuelo__escala_vuelo__isnull=True,
                    reserva__activo=True,
                    reserva__estado__in=[
                        Reserva.EstadoChoices.CONFIRMADA,
                        Reserva.EstadoChoices.RESERVADO_SIN_PAGO
                    ]
                ).values_list('asiento_vuelo__asiento__id', flat=True)
            )
            
            context['asientos'] = asientos_configurados
            context['asientos_ocupados'] = asientos_ocupados
        
        # Tipos de asiento disponibles para filtrado
        tipos_disponibles = AsientoVuelo.objects.filter(
            vuelo=vuelo,
            activo=True,
            habilitado_para_reserva=True
        ).values('tipo_asiento').distinct()
        
        context['tipos_asiento'] = [
            {'value': t['tipo_asiento'], 'label': dict(AsientoVuelo.TipoAsientoChoices.choices)[t['tipo_asiento']]}
            for t in tipos_disponibles
        ]
        
        return context

    def post(self, request, *args, **kwargs):
        vuelo = self.get_object()
        asientos_seleccionados = request.POST.getlist('asientos')
        
        if not asientos_seleccionados:
            messages.error(request, _('Debe seleccionar al menos un asiento'))
            return self.get(request, *args, **kwargs)
        
        try:
            with transaction.atomic():
                # Crear reserva
                reserva = Reserva.objects.create(
                    pasajero=request.user,
                    vuelo=vuelo,
                    estado=Reserva.EstadoChoices.CREADA
                )
                
                # Agregar asientos seleccionados
                precio_total = 0
                for asiento_vuelo_id in asientos_seleccionados:
                    try:
                        asiento_vuelo = AsientoVuelo.objects.get(
                            id=asiento_vuelo_id,
                            vuelo=vuelo,
                            activo=True,
                            habilitado_para_reserva=True
                        )
                        
                        # Verificar disponibilidad
                        if asiento_vuelo.esta_reservado:
                            raise ValidationError(
                                _('El asiento {} ya no está disponible').format(asiento_vuelo.asiento.numero)
                            )
                        
                        ReservaDetalle.objects.create(
                            reserva=reserva,
                            asiento_vuelo=asiento_vuelo,
                            precio_pagado=asiento_vuelo.precio
                        )
                        precio_total += asiento_vuelo.precio
                        
                    except AsientoVuelo.DoesNotExist:
                        raise ValidationError(_('Asiento no válido seleccionado'))
                
                reserva.calcular_precio_total()
                
                messages.success(
                    request,
                    _('Asientos seleccionados exitosamente. Total: ${}'.format(reserva.precio_total))
                )
                
                return redirect('reservas:confirmar_reserva', pk=reserva.pk)
                
        except ValidationError as e:
            messages.error(request, str(e))
            return self.get(request, *args, **kwargs)
        except Exception as e:
            messages.error(request, _('Error al procesar la selección: {}').format(str(e)))
            return self.get(request, *args, **kwargs)


class ConfirmarReservaView(UserRequiredMixin, LoginRequiredMixin, DetailView):
    """Vista para confirmar reserva y elegir método de pago"""
    model = Reserva
    template_name = 'reservas/user/confirmar_reserva.html'
    context_object_name = 'reserva'

    def get_object(self):
        reserva = super().get_object()
        
        # Verificar que sea del usuario actual
        if reserva.pasajero != self.request.user:
            raise Http404()
        
        # Verificar que esté en estado correcto
        if reserva.estado not in [Reserva.EstadoChoices.CREADA]:
            raise Http404(_("Esta reserva no puede ser modificada"))
        
        return reserva

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reserva = self.object() 
        context['boleto'] = None
        context['metodos_pago'] = PagoForm.METODOS_PAGO
        context['total'] = reserva.precio_total
        context['puede_pagar'] = reserva.puede_pagarse
        context['horas_limite'] = reserva.horas_para_expiracion
        context['asientos'] = reserva.detalles.select_related('asiento_vuelo__asiento')
        context['puede_modificar'] = reserva.estado != Reserva.EstadoChoices.CANCELADA
        context['puede_validar_pago'] = reserva.estado in [
            Reserva.EstadoChoices.CREADA, 
            Reserva.EstadoChoices.RESERVADO_SIN_PAGO
        ]
        # Información de asientos
        context['asientos_info'] = []
        for detalle in reserva.detalles.all():
            context['asientos_info'].append({
                'asiento': detalle.asiento_vuelo.asiento,
                'tipo': detalle.asiento_vuelo.tipo_asiento,
                'precio': detalle.precio_pagado
            })
        # Información del vuelo
        context['vuelo'] = reserva.vuelo
        if reserva.vuelo.tiene_escalas:
            context['escalas'] = reserva.vuelo.escalas_vuelo.filter(activo=True).order_by('orden')
        else:
            context['escalas'] = None
        # Información del pasajero
        context['pasajero'] = reserva.pasajero
        # Información adicional
        context['puede_cancelar'] = reserva.estado not in [
            Reserva.EstadoChoices.CONFIRMADA, 
            Reserva.EstadoChoices.CANCELADA
        ]
        context['puede_modificar'] = reserva.estado != Reserva.EstadoChoices.CANCELADA
        context['puede_validar_pago'] = reserva.estado in [
            Reserva.EstadoChoices.CREADA, 
            Reserva.EstadoChoices.RESERVADO_SIN_PAGO
        ]
        return context