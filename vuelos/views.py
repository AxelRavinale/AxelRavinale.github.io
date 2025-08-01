from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import TemplateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView
from django.db.models import Q, Count, Prefetch
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.permissions import AllowAny


from aviones.models import Avion
from vuelos.models import Vuelo, Escala, EscalaVuelo, TripulacionVuelo
from core.models import Localidad, Provincia, Pais, Persona
from vuelos.forms import VueloForm, EscalaVueloFormSet, TripulacionVueloFormSet, VueloFiltroFechaForm
from vuelos.serializers import (
    LocalidadSerializer, AvionSerializer, EscalaSerializer,
    VueloSerializer, TripulacionVueloSerializer
)


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


# ============= TEMPLATE VIEWS =============

class VueloListView(TemplateView):
    template_name = 'vuelos/vuelo_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        form = VueloFiltroFechaForm(self.request.GET or None)
        
        # Queryset base
        vuelos_queryset = Vuelo.objects.select_related(
            'origen_principal', 'destino_principal', 'avion_asignado', 'cargado_por'
        ).prefetch_related(
            Prefetch('escalas_vuelo', queryset=EscalaVuelo.objects.filter(activo=True).order_by('orden')),
            Prefetch('tripulacion', queryset=TripulacionVuelo.objects.filter(activo=True))
        )

        # Filtros adicionales
        activo = self.request.GET.get('activo')
        codigo_vuelo = self.request.GET.get('codigo_vuelo')
        avion = self.request.GET.get('avion')

        # Filtro por estado activo/inactivo
        if activo == '1':
            vuelos_queryset = vuelos_queryset.filter(activo=True)
        elif activo == '0':
            vuelos_queryset = vuelos_queryset.filter(activo=False)
        else:
            # Por defecto mostrar todos, pero puedes cambiar por solo activos si prefieres
            pass

        # Filtro por código de vuelo
        if codigo_vuelo:
            vuelos_queryset = vuelos_queryset.filter(
                codigo_vuelo__icontains=codigo_vuelo
            )

        # Filtro por avión (modelo o matrícula)
        if avion:
            vuelos_queryset = vuelos_queryset.filter(
                Q(avion_asignado__modelo__icontains=avion) |
                Q(avion_asignado__matricula__icontains=avion)
            )

        # Filtros de fecha (tu código existente)
        if form.is_valid():
            fecha_inicio = form.cleaned_data.get('fecha_inicio')
            fecha_fin = form.cleaned_data.get('fecha_fin')

            if fecha_inicio and fecha_fin:
                vuelos_queryset = vuelos_queryset.filter(
                    fecha_salida_estimada__range=(fecha_inicio, fecha_fin)
                )
            elif fecha_inicio:
                vuelos_queryset = vuelos_queryset.filter(
                    fecha_salida_estimada__gte=fecha_inicio
                )
            elif fecha_fin:
                vuelos_queryset = vuelos_queryset.filter(
                    fecha_salida_estimada__lte=fecha_fin
                )

        # Separar vuelos con y sin escalas
        vuelos_sin_escalas = []
        vuelos_con_escalas = []

        for vuelo in vuelos_queryset:
            if vuelo.tiene_escalas:
                vuelos_con_escalas.append(vuelo)
            else:
                vuelos_sin_escalas.append(vuelo)

        localidades = Localidad.objects.filter(activo=True).order_by('nombre')

        context.update({
            'vuelos_sin_escalas': vuelos_sin_escalas,
            'vuelos_con_escalas': vuelos_con_escalas,
            'total_vuelos': len(vuelos_sin_escalas) + len(vuelos_con_escalas),
            'localidades': localidades,
            'form_filtro': form,
        })

        return context


class VueloDetailView(DetailView):
    """Vista detallada de un vuelo específico"""
    model = Vuelo
    template_name = 'vuelos/vuelo_detail.html'
    context_object_name = 'vuelo'
    slug_field = 'codigo_vuelo'
    slug_url_kwarg = 'codigo_vuelo'

    def get_queryset(self):
        return Vuelo.objects.select_related(
            'origen_principal', 'destino_principal', 'avion_asignado', 'cargado_por'
        ).prefetch_related(
            Prefetch('escalas_vuelo', queryset=EscalaVuelo.objects.filter(activo=True).order_by('orden')),
            Prefetch('tripulacion', queryset=TripulacionVuelo.objects.filter(activo=True).select_related('persona'))
        ).filter(activo=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vuelo = self.object
        duracion = vuelo.duracion_total

        if duracion:
            total_seconds = int(duracion.total_seconds())
            days = duracion.days
            hours = (total_seconds // 3600) % 24
            minutes = (total_seconds // 60) % 60

            context.update({
                'duracion_dias': days,
                'duracion_horas': hours,
                'duracion_minutos': minutes,
            })
        else:
            context.update({
                'duracion_dias': None,
                'duracion_horas': None,
                'duracion_minutos': None,
            })

        # Aquí calculamos horas y minutos para cada escala
        escalas = vuelo.escalas_vuelo.all()  # O ajustá según tu relación real
        for escala in escalas:
            if escala.duracion_escala:
                total_seconds = escala.duracion_escala.total_seconds()
                escala.duracion_horas = int(total_seconds // 3600)
                escala.duracion_minutos = int((total_seconds % 3600) // 60)
            else:
                escala.duracion_horas = 0
                escala.duracion_minutos = 0

        context['escalas'] = escalas

        return context


class VueloCreateView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Vista para crear vuelos con escalas y tripulación"""
    template_name = 'vuelos/cargar.html'

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permisos para acceder a esta página.")
        return redirect('vuelo_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.method == 'POST':
            vuelo_form = VueloForm(self.request.POST)
            escala_formset = EscalaVueloFormSet(self.request.POST)
            tripulacion_formset = TripulacionVueloFormSet(self.request.POST)
        else:
            vuelo_form = VueloForm()
            escala_formset = EscalaVueloFormSet()
            tripulacion_formset = TripulacionVueloFormSet()
        
        context.update({
            'vuelo_form': vuelo_form,
            'escala_formset': escala_formset,
            'tripulacion_formset': tripulacion_formset,
            'action': 'create'
        })
        
        return context

    def post(self, request, *args, **kwargs):
        vuelo_form = VueloForm(request.POST)
        escala_formset = EscalaVueloFormSet(request.POST)
        tripulacion_formset = TripulacionVueloFormSet(request.POST)

        if vuelo_form.is_valid() and escala_formset.is_valid() and tripulacion_formset.is_valid():
            # Guardar el vuelo
            vuelo = vuelo_form.save(commit=False)
            vuelo.cargado_por = request.user
            vuelo.km_totales = sum([
            escala_vuelo.escala.km_estimados
                for escala_vuelo in escala_formset.save(commit=False)
                if escala_vuelo.escala
            ])
            vuelo.save()

            # Guardar escalas
            escalas_vuelo = escala_formset.save(commit=False)
            for escala_vuelo in escalas_vuelo:
                escala_vuelo.vuelo = vuelo
                escala_vuelo.save()

            # Guardar tripulación
            tripulacion = tripulacion_formset.save(commit=False)
            for miembro in tripulacion:
                miembro.vuelo = vuelo
                miembro.save()

            # Eliminar objetos marcados para borrar
            for obj in escala_formset.deleted_objects:
                obj.delete()
            for obj in tripulacion_formset.deleted_objects:
                obj.delete()

            messages.success(request, f'Vuelo {vuelo.codigo_vuelo} creado exitosamente.')
            return redirect('vuelo_detail', codigo_vuelo=vuelo.codigo_vuelo)

        # Si hay errores, mostrar el formulario con errores
        context = self.get_context_data()
        context.update({
            'vuelo_form': vuelo_form,
            'escala_formset': escala_formset,
            'tripulacion_formset': tripulacion_formset,
        })
        return self.render_to_response(context)


class VueloUpdateView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Vista para editar vuelos existentes"""
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
            vuelo_form = VueloForm(self.request.POST, instance=vuelo)
            escala_formset = EscalaVueloFormSet(self.request.POST, instance=vuelo)
            tripulacion_formset = TripulacionVueloFormSet(self.request.POST, instance=vuelo)
        else:
            vuelo_form = VueloForm(instance=vuelo)
            escala_formset = EscalaVueloFormSet(instance=vuelo)
            tripulacion_formset = TripulacionVueloFormSet(instance=vuelo)
        
        context.update({
            'vuelo': vuelo,
            'vuelo_form': vuelo_form,
            'escala_formset': escala_formset,
            'tripulacion_formset': tripulacion_formset,
            'action': 'update'
        })
        
        return context

    def post(self, request, *args, **kwargs):
        vuelo = self.get_object()
        vuelo_form = VueloForm(request.POST, instance=vuelo)
        escala_formset = EscalaVueloFormSet(request.POST, instance=vuelo)
        tripulacion_formset = TripulacionVueloFormSet(request.POST, instance=vuelo)

        if vuelo_form.is_valid() and escala_formset.is_valid() and tripulacion_formset.is_valid():
            # Guardar vuelo
            vuelo = vuelo_form.save()

            # Guardar escalas vuelo
            escalas_vuelo = escala_formset.save(commit=False)
            for escala_vuelo in escalas_vuelo:
                escala_vuelo.vuelo = vuelo
                escala_vuelo.save()

            # Guardar tripulación
            tripulacion = tripulacion_formset.save(commit=False)
            for miembro in tripulacion:
                miembro.vuelo = vuelo
                miembro.save()

            # Borrar eliminados
            for obj in escala_formset.deleted_objects:
                obj.delete()
            for obj in tripulacion_formset.deleted_objects:
                obj.delete()

            messages.success(request, f'Vuelo {vuelo.codigo_vuelo} actualizado exitosamente.')
            return redirect('vuelo_detail', codigo_vuelo=vuelo.codigo_vuelo)
        else:
            context = self.get_context_data(
                vuelo_form=vuelo_form,
                escala_formset=escala_formset,
                tripulacion_formset=tripulacion_formset,
            )
            return self.render_to_response(context)


class EscalaCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Vista para crear escalas independientes"""
    model = Escala
    fields = ['origen', 'destino', 'fecha_salida', 'fecha_llegada', 'km_estimados', 'activo']
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
    success_url = reverse_lazy('cargar_vuelo')

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
