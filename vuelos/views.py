from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from vuelos.models import Vuelo, Avion, Escala, TripulacionVuelo
from vuelos.serializers import (
    VueloSerializer, AvionSerializer, EscalaSerializer, TripulacionVueloSerializer
)
from vuelos.repositories import VueloRepository
from vuelos.services import VueloService


# Permisos personalizados
class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class VueloViewSet(viewsets.ModelViewSet):
    queryset = VueloRepository.listar_todos()
    serializer_class = VueloSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        origen = self.request.query_params.get('origen')
        destino = self.request.query_params.get('destino')
        fecha = self.request.query_params.get('fecha')
        return VueloRepository.filtrar(origen, destino, fecha)

    @action(detail=True, methods=['get'])
    def detalle_completo(self, request, pk=None):
        vuelo = VueloRepository.obtener_por_id(pk)
        if not vuelo:
            return Response({'error': 'Vuelo no encontrado'}, status=404)
        data = VueloService.obtener_detalle_completo(vuelo)
        serializer = VueloSerializer(vuelo)
        return Response(serializer.data)


class AvionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Avion.objects.filter(activo=True)
    serializer_class = AvionSerializer


class EscalaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Escala.objects.filter(activo=True)
    serializer_class = EscalaSerializer


class TripulacionVueloViewSet(viewsets.ModelViewSet):
    queryset = TripulacionVuelo.objects.select_related('vuelo', 'persona').all()
    serializer_class = TripulacionVueloSerializer
    permission_classes = [IsAdminOrReadOnly]
