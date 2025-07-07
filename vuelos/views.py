from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from aviones.models import Avion
from vuelos.models import Vuelo, Escala, TripulacionVuelo
from core.models import Localidad

from .serializers import (
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
