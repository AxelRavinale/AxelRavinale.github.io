from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .services import ReporteService

class ReporteViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'], url_path='pasajeros-por-vuelo/(?P<vuelo_id>[^/.]+)')
    def pasajeros_por_vuelo(self, request, vuelo_id=None):
        """Reporte: lista todos los pasajeros de un vuelo"""
        data = ReporteService.obtener_pasajeros_por_vuelo(vuelo_id)
        if data is None:
            return Response({'error': 'Vuelo no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='reservas-activas/(?P<pasajero_id>[^/.]+)')
    def reservas_activas(self, request, pasajero_id=None):
        """Reporte: reservas activas de un pasajero"""
        data = ReporteService.obtener_reservas_activas_por_pasajero(pasajero_id)
        if data is None:
            return Response({'error': 'Pasajero no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        return Response(data, status=status.HTTP_200_OK)
