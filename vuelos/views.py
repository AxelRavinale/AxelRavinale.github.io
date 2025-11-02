from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework.permissions import IsAdminUser, AllowAny

from vuelos.models import Vuelo, Escala, TripulacionVuelo
from vuelos.serializers import (
    VueloSerializer, EscalaSerializer, TripulacionVueloSerializer  # ✅ Eliminé AvionSerializer
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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='origen',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filtrar por origen',
                required=False
            ),
            OpenApiParameter(
                name='destino',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filtrar por destino',
                required=False
            ),
            OpenApiParameter(
                name='fecha',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Filtrar por fecha (YYYY-MM-DD)',
                required=False
            ),
        ]
    )
    def get_queryset(self):
        origen = self.request.query_params.get('origen')
        destino = self.request.query_params.get('destino')
        fecha = self.request.query_params.get('fecha')
        return VueloRepository.filtrar(origen, destino, fecha)

    @extend_schema(
        summary="Obtener detalle completo del vuelo",
        description="Obtiene información detallada de un vuelo específico",
        responses={
            200: VueloSerializer,
            404: OpenApiTypes.OBJECT
        }
    )
    @action(detail=True, methods=['get'])
    def detalle_completo(self, request, pk=None):
        vuelo = VueloRepository.obtener_por_id(pk)
        if not vuelo:
            return Response({'error': 'Vuelo no encontrado'}, status=404)
        data = VueloService.obtener_detalle_completo(vuelo)
        serializer = VueloSerializer(vuelo)
        return Response(serializer.data)


# ❌ ELIMINAR TODA ESTA CLASE AvionViewSet


class EscalaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Escala.objects.filter(activo=True)
    serializer_class = EscalaSerializer


class TripulacionVueloViewSet(viewsets.ModelViewSet):
    queryset = TripulacionVuelo.objects.select_related('vuelo', 'persona').all()
    serializer_class = TripulacionVueloSerializer
    permission_classes = [IsAdminOrReadOnly]