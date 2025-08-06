from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView
from django.db import transaction
from datetime import datetime, time, timedelta
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse_lazy, reverse 
from django.views.generic.edit import CreateView, UpdateView
from django.db.models import Q, Count, Prefetch
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from aviones.models import Avion
from vuelos.models import Vuelo, Escala, EscalaVuelo, TripulacionVuelo, TripulacionEscala
from core.models import Localidad, Provincia, Pais, Persona
from vuelos.forms import (
    VueloInicialForm, EscalaVueloFormSet, TripulacionVueloFormSet, 
    TripulacionEscalaFormSet, VueloFiltroFechaForm
)
from vuelos.serializers import (
    LocalidadSerializer, AvionSerializer, EscalaSerializer,
    VueloSerializer, TripulacionVueloSerializer
)

# ============= VIEWSETS API =============
class LocalidadViewSet(viewsets.ModelViewSet):
    queryset = Localidad.objects.filter(activo=True)
    serializer_class = LocalidadSerializer
    permission_classes = [AllowAny]


class AvionViewSet(viewsets.ModelViewSet):
    queryset = Avion.objects.filter(activo=True)
    serializer_class = AvionSerializer
    permission_classes = [AllowAny]


class EscalaViewSet(viewsets.ModelViewSet):
    queryset = Escala.objects.filter(activo=True)
    serializer_class = EscalaSerializer
    permission_classes = [AllowAny]


class VueloViewSet(viewsets.ModelViewSet):
    queryset = Vuelo.objects.filter(activo=True)
    serializer_class = VueloSerializer
    permission_classes = [AllowAny]


class TripulacionVueloViewSet(viewsets.ModelViewSet):
    queryset = TripulacionVuelo.objects.filter(activo=True)
    serializer_class = TripulacionVueloSerializer
    permission_classes = [AllowAny]


# ============= VISTAS PRINCIPALES =============

# views.py - Vista optimizada para lista de vuelos

from django.views.generic import TemplateView
from django.db.models import Q, Prefetch
from vuelos.models import Vuelo, EscalaVuelo, TripulacionVuelo
from vuelos.forms import VueloFiltroFechaForm

class VueloListView(TemplateView):
    template_name = 'vuelos/vuelo_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        form = VueloFiltroFechaForm(self.request.GET or None)
        form_is_valid = form.is_valid()  # Forzamos la validación

        vuelos_queryset = Vuelo.objects.select_related(
            'origen_principal', 
            'destino_principal', 
            'avion_asignado', 
            'cargado_por'
        ).prefetch_related(
            Prefetch(
                'escalas_vuelo',
                queryset=EscalaVuelo.objects.filter(activo=True)
                    .select_related('escala__origen', 'escala__destino', 'avion')
                    .order_by('orden')
            ),
            Prefetch(
                'tripulacion',
                queryset=TripulacionVuelo.objects.filter(activo=True).select_related('persona')
            )
        )

        # Aplicar filtros
        vuelos_queryset = self._apply_filters(vuelos_queryset, form if form_is_valid else None)

        vuelos_sin_escalas = []
        vuelos_con_escalas = []

        for vuelo in vuelos_queryset:
            vuelo.duracion_calculada = self._calcular_duracion_resumida(vuelo)
            vuelo.total_tripulacion = self._contar_tripulacion_total(vuelo)

            if vuelo.tiene_escalas and vuelo.escalas_vuelo.exists():
                vuelo.escalas_resumen = self._generar_resumen_escalas(vuelo)
                vuelos_con_escalas.append(vuelo)
            else:
                vuelos_sin_escalas.append(vuelo)

        context.update({
            'vuelos_sin_escalas': vuelos_sin_escalas,
            'vuelos_con_escalas': vuelos_con_escalas,
            'total_vuelos': len(vuelos_sin_escalas) + len(vuelos_con_escalas),
            'form_filtro': form,
        })

        return context

    def _apply_filters(self, queryset, form):
        """Aplica todos los filtros al queryset"""
        if not form:
            return queryset.filter(activo=True).order_by('fecha_salida_estimada')

        # Filtro por estado activo/inactivo
        activo = form.cleaned_data.get('activo')
        if activo == '1':
            queryset = queryset.filter(activo=True)
        elif activo == '0':
            queryset = queryset.filter(activo=False)

        # Filtro por código de vuelo
        codigo_vuelo = form.cleaned_data.get('codigo_vuelo')
        if codigo_vuelo:
            queryset = queryset.filter(codigo_vuelo__icontains=codigo_vuelo)

        # Filtro por avión
        avion = form.cleaned_data.get('avion')
        if avion:
            queryset = queryset.filter(
                Q(avion_asignado__modelo__icontains=avion) |
                Q(avion_asignado__matricula__icontains=avion)
            )

        # Filtro por fecha
        fecha_inicio = form.cleaned_data.get('fecha_inicio')
        fecha_fin = form.cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin:
            fecha_inicio_dt = datetime.combine(fecha_inicio, time.min)
            fecha_fin_dt = datetime.combine(fecha_fin, time.max)
            queryset = queryset.filter(
                fecha_salida_estimada__range=(fecha_inicio_dt, fecha_fin_dt)
            )
        elif fecha_inicio:
            fecha_inicio_dt = datetime.combine(fecha_inicio, time.min)
            queryset = queryset.filter(fecha_salida_estimada__gte=fecha_inicio_dt)
        elif fecha_fin:
            fecha_fin_dt = datetime.combine(fecha_fin, time.max)
            queryset = queryset.filter(fecha_salida_estimada__lte=fecha_fin_dt)

        return queryset.order_by('fecha_salida_estimada')

    def _calcular_duracion_resumida(self, vuelo):
        """Calcula duración en formato resumido"""
        if not vuelo.duracion_total:
            return "N/A"
        total_seconds = int(vuelo.duracion_total.total_seconds())
        days = vuelo.duracion_total.days
        hours = (total_seconds // 3600) % 24
        minutes = (total_seconds // 60) % 60

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    def _contar_tripulacion_total(self, vuelo):
        """Cuenta el total de tripulación del vuelo"""
        if vuelo.tiene_escalas:
            tripulacion_ids = set()
            for escala in vuelo.escalas_vuelo.all():
                for tripulante in escala.tripulacion_escala.filter(activo=True):
                    tripulacion_ids.add(tripulante.persona_id)
            return len(tripulacion_ids)
        return vuelo.tripulacion.filter(activo=True).count()

    def _generar_resumen_escalas(self, vuelo):
        """Genera un resumen de las escalas para mostrar en la lista"""
        escalas = vuelo.escalas_vuelo.all()[:3]
        resumen = []
        for escala in escalas:
            resumen.append({
                'orden': escala.orden,
                'ruta': f"{escala.escala.origen.nombre} → {escala.escala.destino.nombre}",
                'avion': f"{escala.avion.modelo}",
                'tripulacion_count': escala.tripulacion_escala.filter(activo=True).count()
            })
        return {
            'escalas': resumen,
            'tiene_mas': vuelo.escalas_vuelo.count() > 3,
            'total': vuelo.escalas_vuelo.count()
        }


# views.py - Vista optimizada para detalle de vuelo

class VueloDetailView(DetailView):
    """Vista detallada de un vuelo específico con toda la información organizada"""
    model = Vuelo
    template_name = 'vuelos/vuelo_detail.html'
    context_object_name = 'vuelo'
    slug_field = 'codigo_vuelo'
    slug_url_kwarg = 'codigo_vuelo'

    def get_queryset(self):
        return Vuelo.objects.select_related(
            'origen_principal__provincia__pais',
            'destino_principal__provincia__pais', 
            'avion_asignado', 
            'cargado_por'
        ).prefetch_related(
            # Escalas con toda la información necesaria
            Prefetch(
                'escalas_vuelo', 
                queryset=EscalaVuelo.objects.filter(activo=True)
                .select_related(
                    'escala__origen__provincia__pais',
                    'escala__destino__provincia__pais',
                    'avion'
                )
                .prefetch_related(
                    Prefetch(
                        'tripulacion_escala',
                        queryset=TripulacionEscala.objects.filter(activo=True)
                        .select_related('persona')
                        .order_by('rol', 'persona__apellido')
                    )
                )
                .order_by('orden')
            ),
            # Tripulación general (solo para vuelos sin escalas)
            Prefetch(
                'tripulacion', 
                queryset=TripulacionVuelo.objects.filter(activo=True)
                .select_related('persona')
                .order_by('rol', 'persona__apellido')
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vuelo = self.object

        # Información de duración
        duracion_info = self._calcular_duraciones(vuelo)
        context.update(duracion_info)

        # Organizar información según tipo de vuelo
        if vuelo.tiene_escalas and vuelo.escalas_vuelo.exists():
            context.update(self._procesar_vuelo_con_escalas(vuelo))
        else:
            context.update(self._procesar_vuelo_directo(vuelo))

        # Métricas generales
        context.update({
            'metricas': self._calcular_metricas(vuelo),
            'tipo_vuelo': 'con_escalas' if vuelo.tiene_escalas else 'directo'
        })

        return context

    def _calcular_duraciones(self, vuelo):
        """Calcula todas las duraciones del vuelo"""
        duraciones = {
            'duracion_dias': None,
            'duracion_horas': None,
            'duracion_minutos': None,
        }

        if vuelo.duracion_total:
            total_seconds = int(vuelo.duracion_total.total_seconds())
            duraciones.update({
                'duracion_dias': vuelo.duracion_total.days,
                'duracion_horas': (total_seconds // 3600) % 24,
                'duracion_minutos': (total_seconds // 60) % 60,
            })

        return duraciones

    def _procesar_vuelo_con_escalas(self, vuelo):
        """Procesa la información de un vuelo con escalas"""
        escalas_procesadas = []
        tripulacion_total = set()
        distancia_total = 0

        for escala in vuelo.escalas_vuelo.all():
            # Procesar cada escala
            escala_info = {
                'escala': escala,
                'duracion_info': self._calcular_duracion_escala(escala),
                'tripulacion': self._organizar_tripulacion_escala(escala),
                'ubicaciones': {
                    'origen_completo': self._formato_ubicacion_completa(escala.escala.origen),
                    'destino_completo': self._formato_ubicacion_completa(escala.escala.destino),
                }
            }
            escalas_procesadas.append(escala_info)
            
            # Agregar tripulación al total (sin duplicados)
            for tripulante in escala.tripulacion_escala.filter(activo=True):
                tripulacion_total.add((tripulante.persona.id, tripulante.persona))
            
            distancia_total += escala.escala.km_estimados

        return {
            'escalas_detalladas': escalas_procesadas,
            'resumen_escalas': {
                'total_escalas': len(escalas_procesadas),
                'distancia_total': distancia_total,
                'tripulacion_unica': len(tripulacion_total),
                'personas_involucradas': [persona for _, persona in tripulacion_total]
            }
        }

    def _procesar_vuelo_directo(self, vuelo):
        """Procesa la información de un vuelo directo"""
        tripulacion_organizada = self._organizar_tripulacion_vuelo(vuelo.tripulacion.filter(activo=True))
        
        return {
            'vuelo_directo': {
                'tripulacion': tripulacion_organizada,
                'ubicaciones': {
                    'origen_completo': self._formato_ubicacion_completa(vuelo.origen_principal),
                    'destino_completo': self._formato_ubicacion_completa(vuelo.destino_principal),
                }
            }
        }

    def _calcular_duracion_escala(self, escala):
        """Calcula la duración de una escala específica"""
        if not escala.duracion_escala:
            return {'horas': 0, 'minutos': 0}
        
        total_seconds = escala.duracion_escala.total_seconds()
        return {
            'horas': int(total_seconds // 3600),
            'minutos': int((total_seconds % 3600) // 60)
        }

    def _organizar_tripulacion_escala(self, escala):
        """Organiza la tripulación de una escala por roles"""
        tripulacion_por_rol = {}
        for tripulante in escala.tripulacion_escala.filter(activo=True):
            rol = tripulante.get_rol_display()
            if rol not in tripulacion_por_rol:
                tripulacion_por_rol[rol] = []
            tripulacion_por_rol[rol].append(tripulante)
        
        return tripulacion_por_rol

    def _organizar_tripulacion_vuelo(self, tripulacion_queryset):
        """Organiza la tripulación de un vuelo directo por roles"""
        tripulacion_por_rol = {}
        for tripulante in tripulacion_queryset:
            rol = tripulante.get_rol_display()
            if rol not in tripulacion_por_rol:
                tripulacion_por_rol[rol] = []
            tripulacion_por_rol[rol].append(tripulante)
        
        return tripulacion_por_rol

    def _formato_ubicacion_completa(self, localidad):
        """Formatea la ubicación completa con provincia y país"""
        if not localidad:
            return "No especificada"
        
        ubicacion = localidad.nombre
        if localidad.provincia:
            ubicacion += f", {localidad.provincia.nombre}"
            if localidad.provincia.pais:
                ubicacion += f", {localidad.provincia.pais.nombre}"
        
        return ubicacion

    def _calcular_metricas(self, vuelo):
        """Calcula métricas importantes del vuelo"""
        metricas = {
            'distancia_real': vuelo.distancia_recorrida or vuelo.km_totales or 0,
            'numero_escalas': vuelo.numero_escalas,
            'total_tripulacion': 0,
            'aviones_utilizados': set(),
        }

        if vuelo.tiene_escalas:
            # Contar tripulación única y aviones de escalas
            tripulacion_unica = set()
            for escala in vuelo.escalas_vuelo.filter(activo=True):
                metricas['aviones_utilizados'].add(escala.avion.id)
                for tripulante in escala.tripulacion_escala.filter(activo=True):
                    tripulacion_unica.add(tripulante.persona.id)
            metricas['total_tripulacion'] = len(tripulacion_unica)
        else:
            # Vuelo directo
            metricas['total_tripulacion'] = vuelo.tripulacion.filter(activo=True).count()
            if vuelo.avion_asignado:
                metricas['aviones_utilizados'].add(vuelo.avion_asignado.id)

        metricas['total_aviones'] = len(metricas['aviones_utilizados'])
        return metricas

# ============= PASO 1: CREAR VUELO INICIAL =============

class VueloCreateView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Vista para crear vuelo inicial (solo datos básicos)"""
    template_name = 'vuelos/cargar.html'

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permisos para acceder a esta página.")
        return redirect('vuelo_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        vuelo_form = VueloInicialForm()
        
        context.update({
            'vuelo_form': vuelo_form,
            'action': 'create'
        })
        
        return context

    def post(self, request, *args, **kwargs):
        vuelo_form = VueloInicialForm(request.POST)

        if vuelo_form.is_valid():
            vuelo = vuelo_form.save(commit=False)
            vuelo.cargado_por = request.user
            vuelo.save()

            messages.success(request, f'Vuelo {vuelo.codigo_vuelo} creado exitosamente.')

            # Redirigir según tenga escalas o no
            if vuelo.tiene_escalas:
                return redirect('vuelo_escalas', codigo_vuelo=vuelo.codigo_vuelo)
            else:
                return redirect('vuelo_tripulacion', codigo_vuelo=vuelo.codigo_vuelo)

        # Si el formulario tiene errores, renderizar la misma plantilla con el form con errores
        return self.render_to_response({
            'vuelo_form': vuelo_form,
            'action': 'create'
        })


# ============= PASO 2A: GESTIONAR ESCALAS =============

class VueloEscalasView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Vista para gestionar escalas de un vuelo"""
    template_name = 'vuelos/vuelo_escalas.html'

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permisos para acceder a esta página.")
        return redirect('vuelo_list')

    def get_object(self):
        return get_object_or_404(Vuelo, codigo_vuelo=self.kwargs['codigo_vuelo'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vuelo = self.get_object()
        
        if self.request.method == 'POST':
            escala_formset = EscalaVueloFormSet(self.request.POST, instance=vuelo)
        else:
            escala_formset = EscalaVueloFormSet(instance=vuelo)
        
        context.update({
            'vuelo': vuelo,
            'escala_formset': escala_formset,
            'action': 'escalas'
        })
        
        return context

    def post(self, request, *args, **kwargs):
        vuelo = self.get_object()
        escala_formset = EscalaVueloFormSet(request.POST, instance=vuelo)
        
        # Obtener la acción del formulario
        action = request.POST.get('action', 'save_and_continue')

        if escala_formset.is_valid():
            # Guardar escalas
            escalas_vuelo = escala_formset.save(commit=False)
            for escala_vuelo in escalas_vuelo:
                escala_vuelo.vuelo = vuelo
                escala_vuelo.save()

            # Eliminar objetos marcados para borrar
            for obj in escala_formset.deleted_objects:
                obj.delete()

            # Determinar mensaje y redirección según la acción
            if action == 'save_and_stay':
                messages.success(request, f'Escalas del vuelo {vuelo.codigo_vuelo} guardadas. Puede agregar más escalas.')
                # Redirigir a la misma página para agregar más escalas
                return redirect('vuelo_escalas', codigo_vuelo=vuelo.codigo_vuelo)
            else:  # save_and_continue
                messages.success(request, f'Escalas del vuelo {vuelo.codigo_vuelo} guardadas exitosamente.')
                # CORRECCIÓN: Continuar al siguiente paso (tripulación de escalas)
                return redirect('vuelo_tripulacion_escala', codigo_vuelo=vuelo.codigo_vuelo)

        # Si hay errores, mostrar el formulario con errores
        context = self.get_context_data()
        context['escala_formset'] = escala_formset
        messages.error(request, 'Por favor corrija los errores en el formulario.')
        return self.render_to_response(context)
    

class VueloTripulacionEscalasView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Vista para gestionar tripulación de una escala específica de un vuelo"""
    template_name = 'vuelos/vuelo_tripulacion_escala.html'

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permisos para acceder a esta página.")
        return redirect('vuelo_list')

    def get_object(self):
        return get_object_or_404(Vuelo, codigo_vuelo=self.kwargs['codigo_vuelo'])
    
    def get_escala(self):
        """Obtiene la escala específica según el orden"""
        vuelo = self.get_object()
        orden = self.kwargs['orden']
        return get_object_or_404(
            EscalaVuelo, 
            vuelo=vuelo, 
            orden=orden,
            activo=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vuelo = self.get_object()
        escala_actual = self.get_escala()
        
        # Obtener todas las escalas para navegación
        todas_las_escalas = vuelo.escalas_vuelo.filter(activo=True).order_by('orden')
        
        formset = TripulacionEscalaFormSet(
            instance=escala_actual,
            prefix=f'escala_{escala_actual.id}'
        )
        
        # Determinar navegación
        escalas_list = list(todas_las_escalas)
        current_index = None
        for i, escala in enumerate(escalas_list):
            if escala.orden == escala_actual.orden:
                current_index = i
                break
        
        escala_anterior = escalas_list[current_index - 1] if current_index and current_index > 0 else None
        escala_siguiente = escalas_list[current_index + 1] if current_index is not None and current_index < len(escalas_list) - 1 else None
        
        context.update({
            'vuelo': vuelo,
            'escala_actual': escala_actual,
            'formset': formset,
            'todas_las_escalas': todas_las_escalas,
            'escala_anterior': escala_anterior,
            'escala_siguiente': escala_siguiente,
            'es_primera_escala': current_index == 0,
            'es_ultima_escala': current_index == len(escalas_list) - 1 if current_index is not None else False,
            'total_escalas': len(escalas_list),
            'escala_numero': current_index + 1 if current_index is not None else 1,
            'action': 'tripulacion_escala'
        })
        
        return context

    def post(self, request, *args, **kwargs):
        vuelo = self.get_object()
        escala_actual = self.get_escala()
        
        # Crear formset para la escala actual
        formset = TripulacionEscalaFormSet(
            request.POST, 
            instance=escala_actual,
            prefix=f'escala_{escala_actual.id}'
        )
        
        # Obtener la acción del formulario
        action = request.POST.get('action', 'save_and_continue')
        
        if formset.is_valid():
            # Guardar tripulación de la escala
            tripulacion_escalas = formset.save(commit=False)
            for tripulacion_escala in tripulacion_escalas:
                tripulacion_escala.escala_vuelo = escala_actual
                tripulacion_escala.save()

            # Eliminar objetos marcados para borrar
            for obj in formset.deleted_objects:
                obj.delete()

            if action == 'save_and_stay':
                messages.success(request, f'Tripulación de la escala {escala_actual.orden} guardada exitosamente.')
                return redirect('vuelo_tripulacion_escalas', 
                              codigo_vuelo=vuelo.codigo_vuelo, 
                              orden=escala_actual.orden)
            
            elif action == 'save_and_next':
                # Ir a la siguiente escala
                siguiente_escala = EscalaVuelo.objects.filter(
                    vuelo=vuelo, 
                    orden__gt=escala_actual.orden,
                    activo=True
                ).order_by('orden').first()
                
                if siguiente_escala:
                    messages.success(request, f'Tripulación de la escala {escala_actual.orden} guardada. Configurando escala {siguiente_escala.orden}.')
                    return redirect('vuelo_tripulacion_escalas', 
                                  codigo_vuelo=vuelo.codigo_vuelo, 
                                  orden=siguiente_escala.orden)
                else:
                    messages.success(request, f'Tripulación de la escala {escala_actual.orden} guardada. Todas las escalas configuradas.')
                    return redirect('vuelo_detail', codigo_vuelo=vuelo.codigo_vuelo)
            
            elif action == 'save_and_previous':
                # Ir a la escala anterior
                anterior_escala = EscalaVuelo.objects.filter(
                    vuelo=vuelo, 
                    orden__lt=escala_actual.orden,
                    activo=True
                ).order_by('-orden').first()
                
                if anterior_escala:
                    messages.success(request, f'Tripulación de la escala {escala_actual.orden} guardada. Configurando escala {anterior_escala.orden}.')
                    return redirect('vuelo_tripulacion_escalas', 
                                  codigo_vuelo=vuelo.codigo_vuelo, 
                                  orden=anterior_escala.orden)
                else:
                    messages.success(request, f'Tripulación de la escala {escala_actual.orden} guardada.')
                    return redirect('vuelo_tripulacion_escalas', 
                                  codigo_vuelo=vuelo.codigo_vuelo, 
                                  orden=escala_actual.orden)
            
            else:  # save_and_finish
                messages.success(request, f'Tripulación de la escala {escala_actual.orden} guardada exitosamente.')
                return redirect('vuelo_detail', codigo_vuelo=vuelo.codigo_vuelo)

        # Si hay errores, mostrar el formulario con errores
        context = self.get_context_data()
        context['formset'] = formset
        messages.error(request, 'Por favor corrija los errores en el formulario.')
        return self.render_to_response(context)


class VueloTripulacionView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Vista para gestionar tripulación de un vuelo directo (sin escalas)"""
    template_name = 'vuelos/vuelo_tripulacion.html'

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permisos para acceder a esta página.")
        return redirect('vuelo_list')

    def get_object(self):
        return get_object_or_404(Vuelo, codigo_vuelo=self.kwargs['codigo_vuelo'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vuelo = self.get_object()
        
        if vuelo.tiene_escalas:
            messages.warning(self.request, f"El vuelo {vuelo.codigo_vuelo} tiene escalas configuradas. Use la gestión de tripulación por escalas.")
            return redirect('vuelo_detail', codigo_vuelo=vuelo.codigo_vuelo)

        # 🚫 Nunca usar self.request.method aquí
        formset = TripulacionVueloFormSet(instance=vuelo, prefix='tripulacion')

        context.update({
            'vuelo': vuelo,
            'formset': formset,
            'action': 'tripulacion_vuelo'
        })
        return context

    def get(self, request, *args, **kwargs):
        vuelo = self.get_object()
        if vuelo.tiene_escalas:
            messages.warning(request, f"El vuelo {vuelo.codigo_vuelo} tiene escalas configuradas. Use la gestión de tripulación por escalas.")
            return redirect('vuelo_detail', codigo_vuelo=vuelo.codigo_vuelo)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        vuelo = self.get_object()

        if vuelo.tiene_escalas:
            messages.warning(request, f"El vuelo {vuelo.codigo_vuelo} tiene escalas configuradas. Use la gestión de tripulación por escalas.")
            return redirect('vuelo_detail', codigo_vuelo=vuelo.codigo_vuelo)

        formset = TripulacionVueloFormSet(request.POST, instance=vuelo, prefix='tripulacion')
        action = request.POST.get('action', 'save_and_finish')

        if formset.is_valid():
            try:
                with transaction.atomic():
                    tripulacion_miembros = formset.save(commit=False)
                    for tripulacion in tripulacion_miembros:
                        tripulacion.vuelo = vuelo
                        tripulacion.save()

                    for obj in formset.deleted_objects:
                        obj.delete()

                if action == 'save_and_stay':
                    messages.success(request, f'Tripulación del vuelo {vuelo.codigo_vuelo} guardada exitosamente. Puede continuar editando.')
                    return redirect('vuelo_tripulacion', codigo_vuelo=vuelo.codigo_vuelo)
                elif action == 'save_and_finish':
                    messages.success(request, f'Tripulación del vuelo {vuelo.codigo_vuelo} guardada exitosamente.')
                    return redirect('vuelo_detail', codigo_vuelo=vuelo.codigo_vuelo)
                else:
                    messages.success(request, f'Tripulación del vuelo {vuelo.codigo_vuelo} guardada exitosamente. Puede continuar editando.')
                    return redirect('vuelo_tripulacion', codigo_vuelo=vuelo.codigo_vuelo)

            except Exception as e:
                messages.error(request, f'Ocurrió un error al guardar la tripulación: {str(e)}')
        else:
            messages.error(request, 'Hay errores en el formulario de tripulación.')

        # ✅ Volver a mostrar el formset con errores manualmente
        context = super().get_context_data(**kwargs)
        context.update({
            'vuelo': vuelo,
            'formset': formset,
            'action': 'tripulacion_vuelo'
        })
        return self.render_to_response(context)


# ============= PASO 3: GESTIONAR TRIPULACIÓN DE ESCALAS =============


# ============= VISTAS DE EDICIÓN =============

class VueloUpdateView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Vista para editar vuelos existentes con escalas y tripulación"""
    template_name = 'vuelos/update_vuelo.html'

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permisos para acceder a esta página.")
        return redirect('vuelo_list')

    def get_object(self):
        return get_object_or_404(Vuelo, codigo_vuelo=self.kwargs['codigo_vuelo'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vuelo = self.get_object()
        
        if self.request.method == 'POST':
            vuelo_form = VueloInicialForm(self.request.POST, instance=vuelo)
            escala_formset = EscalaVueloFormSet(self.request.POST, instance=vuelo)
            tripulacion_formset = TripulacionVueloFormSet(self.request.POST, instance=vuelo)
        else:
            vuelo_form = VueloInicialForm(instance=vuelo)
            escala_formset = EscalaVueloFormSet(instance=vuelo)
            tripulacion_formset = TripulacionVueloFormSet(instance=vuelo)
        
        # Agregar datos adicionales para el template
        escalas_disponibles = Escala.objects.filter(activo=True)
        aviones_disponibles = Avion.objects.filter(activo=True)
        personas_disponibles = Persona.objects.filter(activo=True)
        
        context.update({
            'vuelo': vuelo,
            'vuelo_form': vuelo_form,
            'escala_formset': escala_formset,
            'tripulacion_formset': tripulacion_formset,
            'escalas_disponibles': escalas_disponibles,
            'aviones_disponibles': aviones_disponibles,
            'personas_disponibles': personas_disponibles,
            'action': 'update'
        })
        
        return context

    def post(self, request, *args, **kwargs):
        vuelo = self.get_object()
        vuelo_form = VueloInicialForm(request.POST, instance=vuelo)
        escala_formset = EscalaVueloFormSet(request.POST, instance=vuelo)
        tripulacion_formset = TripulacionVueloFormSet(request.POST, instance=vuelo)

        # Validar todos los formularios
        vuelo_valid = vuelo_form.is_valid()
        escalas_valid = escala_formset.is_valid()
        tripulacion_valid = tripulacion_formset.is_valid()

        if vuelo_valid and escalas_valid and tripulacion_valid:

            try:
                # Guardar vuelo principal
                vuelo = vuelo_form.save()

                # Guardar escalas
                escalas = escala_formset.save(commit=False)
                for escala in escalas:
                    escala.vuelo = vuelo
                    escala.save()

                # Eliminar escalas marcadas para eliminación
                for escala in escala_formset.deleted_objects:
                    escala.delete()

                # Guardar tripulación
                tripulacion = tripulacion_formset.save(commit=False)
                for miembro in tripulacion:
                    miembro.vuelo = vuelo
                    miembro.save()

                # Eliminar tripulación marcada para eliminación
                for miembro in tripulacion_formset.deleted_objects:
                    miembro.delete()

                messages.success(request, f'Vuelo {vuelo.codigo_vuelo} actualizado exitosamente con todas sus escalas y tripulación.')
                return redirect('vuelo_detail', codigo_vuelo=vuelo.codigo_vuelo)

            except Exception as e:
                messages.error(request, f'Error al actualizar el vuelo: {str(e)}')
        else:
            # Mostrar errores específicos
            if not vuelo_valid:
                messages.error(request, 'Hay errores en la información del vuelo.')
            if not escalas_valid:
                messages.error(request, 'Hay errores en las escalas del vuelo.')
            if not tripulacion_valid:
                messages.error(request, 'Hay errores en la tripulación del vuelo.')

        # Si hay errores, mostrar el formulario con errores
        context = self.get_context_data()
        context.update({
            'vuelo_form': vuelo_form,
            'escala_formset': escala_formset,
            'tripulacion_formset': tripulacion_formset,
        })
        return self.render_to_response(context)

# ============= VISTAS AUXILIARES =============

class EscalaCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Vista para crear escalas independientes"""
    model = Escala
    fields = ['origen', 'destino', 'km_estimados', 'activo']
    template_name = 'vuelos/escala_form.html'
    success_url = reverse_lazy('vuelo_create')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permiso para crear escalas.")
        return redirect('vuelo_list')

    def form_valid(self, form):
        messages.success(self.request, "Escala creada correctamente.")
        return super().form_valid(form)

    
class PaisCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Pais
    fields = ['nombre', 'activo']
    template_name = 'vuelos/pais_form.html'
    success_url = reverse_lazy('pais_form')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("No tienes permiso para crear países.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['paises'] = Pais.objects.order_by('nombre')
        return context

    
class ProvinciaCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Provincia
    fields = ['pais', 'nombre', 'activo']
    template_name = 'vuelos/provincia_form.html'
    success_url = reverse_lazy('provincia_form')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("No tienes permiso para crear provincias.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['provincias'] = Provincia.objects.select_related('pais').order_by('pais__nombre', 'nombre')
        return context

    
class LocalidadCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Localidad
    fields = ['nombre', 'provincia', 'activo']
    template_name = 'vuelos/localidad_form.html'
    success_url = reverse_lazy('vuelo_create')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("No tienes permiso para crear localidades.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['localidades'] = Localidad.objects.select_related('provincia__pais').order_by('provincia__pais__nombre', 'provincia__nombre', 'nombre')
        return context


def listar_vuelos(request):
    vuelos = Vuelo.objects.all()
    return render(request, 'tu_template.html', {'vuelos': vuelos})