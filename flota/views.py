from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .serializers import AvionSerializer
from .services import AvionService

class AvionPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

class AvionViewSet(viewsets.ViewSet):
    """
    CRUD completo para la gestión de aviones.
    Solo administradores pueden crear, editar o eliminar.
    """

    pagination_class = AvionPagination

    def list(self, request):
        aviones = AvionService.listar_aviones()
        paginator = self.pagination_class()
        resultados = paginator.paginate_queryset(aviones, request)
        serializer = AvionSerializer(resultados, many=True)
        return paginator.get_paginated_response(serializer.data)

    def retrieve(self, request, pk=None):
        avion = AvionService.obtener_avion(pk)
        if not avion:
            return Response({'error': 'Avión no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AvionSerializer(avion).data)

    def create(self, request):
        serializer = AvionSerializer(data=request.data)
        if serializer.is_valid():
            avion = AvionService.registrar_avion(serializer.validated_data)
            return Response({
                'message': 'Avión registrado correctamente',
                'avion': AvionSerializer(avion).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        serializer = AvionSerializer(data=request.data)
        if serializer.is_valid():
            avion = AvionService.actualizar_avion(pk, serializer.validated_data)
            if not avion:
                return Response({'error': 'Avión no encontrado'}, status=status.HTTP_404_NOT_FOUND)
            return Response({
                'message': 'Avión actualizado correctamente',
                'avion': AvionSerializer(avion).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        eliminado = AvionService.eliminar_avion(pk)
        if not eliminado:
            return Response({'error': 'Avión no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'message': 'Avión eliminado correctamente'}, status=status.HTTP_204_NO_CONTENT)
