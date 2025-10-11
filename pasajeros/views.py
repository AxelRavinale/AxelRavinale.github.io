from rest_framework.decorators import action
from rest_framework import status, viewsets
from rest_framework.response import Response
from pasajeros.serializers import PasajeroSerializer
from pasajeros.services import PasajeroService

class PasajeroViewSet(viewsets.ViewSet):
    def list(self, request):
        pasajeros = PasajeroService.listar_pasajeros()
        serializer = PasajeroSerializer(pasajeros, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        pasajero = PasajeroService.obtener_pasajero(pk)
        if not pasajero:
            return Response({'error': 'Pasajero no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        serializer = PasajeroSerializer(pasajero)
        return Response(serializer.data)

    def create(self, request):
        serializer = PasajeroSerializer(data=request.data)
        if serializer.is_valid():
            pasajero = PasajeroService.registrar_pasajero(serializer.validated_data)
            return Response(PasajeroSerializer(pasajero).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        pasajero = PasajeroService.obtener_pasajero(pk)
        if not pasajero:
            return Response({'error': 'Pasajero no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        serializer = PasajeroSerializer(pasajero, data=request.data, partial=True)
        if serializer.is_valid():
            pasajero = PasajeroService.editar_pasajero(pasajero, serializer.validated_data)
            return Response(PasajeroSerializer(pasajero).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        pasajero = PasajeroService.obtener_pasajero(pk)
        if not pasajero:
            return Response({'error': 'Pasajero no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        PasajeroService.eliminar_pasajero(pasajero)
        return Response({'message': 'Pasajero eliminado correctamente.'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def reservas(self, request, pk=None):
        """Lista las reservas asociadas a un pasajero"""
        reservas = PasajeroService.listar_reservas_por_pasajero(pk)
        if reservas is None:
            return Response({'error': 'Pasajero no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        return Response(reservas, status=status.HTTP_200_OK)