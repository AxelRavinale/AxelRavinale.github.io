from .models import Vuelo
from django.db.models import Q, Prefetch
from .models import EscalaVuelo, TripulacionVuelo

class VueloRepository:
    @staticmethod
    def listar_todos():
        return Vuelo.objects.filter(activo=True).select_related('avion')

    @staticmethod
    def obtener_por_id(pk):
        return Vuelo.objects.select_related('avion').prefetch_related(
            Prefetch('escalas_vuelo'),
            Prefetch('tripulacion_vuelo')
        ).filter(pk=pk, activo=True).first()

    @staticmethod
    def filtrar(origen=None, destino=None, fecha=None):
        queryset = Vuelo.objects.filter(activo=True)
        if origen:
            queryset = queryset.filter(origen__icontains=origen)
        if destino:
            queryset = queryset.filter(destino__icontains=destino)
        if fecha:
            queryset = queryset.filter(fecha_salida__date=fecha)
        return queryset.select_related('avion')
