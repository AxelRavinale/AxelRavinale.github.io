from django.shortcuts import render
from django.views.generic import TemplateView 
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView

from aviones.models import Avion
from vuelos.models import Vuelo, Escala, TripulacionVuelo
from core.models import Localidad
from vuelos.forms import VueloForm

from vuelos.serializers import (
    LocalidadSerializer, AvionSerializer, EscalaSerializer,
    VueloSerializer, TripulacionVueloSerializer
)

class LocalidadViewSet(viewsets.ModelViewSet):
    queryset = Localidad.objects.all()
    serializer_class = LocalidadSerializer
    permission_classes = [AllowAny]


class AvionViewSet(viewsets.ModelViewSet):
    queryset = Avion.objects.all()
    serializer_class = AvionSerializer
    permission_classes = [AllowAny]


class EscalaViewSet(viewsets.ModelViewSet):
    queryset = Escala.objects.all()
    serializer_class = EscalaSerializer
    permission_classes = [AllowAny]


class VueloViewSet(viewsets.ModelViewSet):
    queryset = Vuelo.objects.all()
    serializer_class = VueloSerializer
    permission_classes = [AllowAny]


class TripulacionVueloViewSet(viewsets.ModelViewSet):
    queryset = TripulacionVuelo.objects.all()
    serializer_class = TripulacionVueloSerializer
    permission_classes = [AllowAny]


class VueloTemplateView(TemplateView):
    template_name = 'vuelos/vuelo_list.html'  

class DetailVueloTemplateView(TemplateView):
    model = Vuelo
    template_name = 'vuelos/vuelo_detail.html'
    context_object_name = 'vuelo'  

class VueloCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Vuelo
    form_class = VueloForm
    template_name = 'vuelos/cargar.html'
    success_url = reverse_lazy('vista_vuelos')  # Cambiá si tenés otro nombre

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        from django.contrib import messages
        messages.error(self.request, "No tenés permisos para acceder a esta página.")
        from django.shortcuts import redirect
        return redirect('home')  
    

class EscalaCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Escala
    fields = ['origen', 'destino', 'fecha_salida', 'fecha_llegada', 'km_estimados', 'activo']
    template_name = 'vuelos/escala_form.html'
    success_url = reverse_lazy('vuelo_create')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("No tienes permiso para crear escalas.")
    
class LocalidadCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Localidad
    fields = ['nombre', 'activo']
    template_name = 'vuelos/localidad_form.html'  
    success_url = reverse_lazy('cargar_vuelo') 

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("No tienes permiso para crear localidades.")