from rest_framework.decorators import action
from rest_framework import status, viewsets
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from pasajeros.serializers import PasajeroSerializer
from pasajeros.services import PasajeroService

class PasajeroViewSet(viewsets.ViewSet):
    
    @extend_schema(
        summary="Listar todos los pasajeros",
        description="Obtiene una lista de todos los pasajeros registrados",
        responses={200: PasajeroSerializer(many=True)}
    )
    def list(self, request):
        pasajeros = PasajeroService.listar_pasajeros()
        serializer = PasajeroSerializer(pasajeros, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Obtener un pasajero específico",
        description="Obtiene los detalles de un pasajero por su ID",
        responses={
            200: PasajeroSerializer,
            404: OpenApiTypes.OBJECT
        }
    )
    def retrieve(self, request, pk=None):
        pasajero = PasajeroService.obtener_pasajero(pk)
        if not pasajero:
            return Response({'error': 'Pasajero no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        serializer = PasajeroSerializer(pasajero)
        return Response(serializer.data)

    @extend_schema(
        summary="Crear un nuevo pasajero",
        description="Registra un nuevo pasajero en el sistema",
        request=PasajeroSerializer,
        responses={
            201: PasajeroSerializer,
            400: OpenApiTypes.OBJECT
        }
    )
    def create(self, request):
        serializer = PasajeroSerializer(data=request.data)
        if serializer.is_valid():
            pasajero = PasajeroService.registrar_pasajero(serializer.validated_data)
            return Response(PasajeroSerializer(pasajero).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Actualizar un pasajero",
        description="Actualiza los datos de un pasajero existente (actualización parcial permitida)",
        request=PasajeroSerializer,
        responses={
            200: PasajeroSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        }
    )
    def update(self, request, pk=None):
        pasajero = PasajeroService.obtener_pasajero(pk)
        if not pasajero:
            return Response({'error': 'Pasajero no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        serializer = PasajeroSerializer(pasajero, data=request.data, partial=True)
        if serializer.is_valid():
            pasajero = PasajeroService.editar_pasajero(pasajero, serializer.validated_data)
            return Response(PasajeroSerializer(pasajero).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Eliminar un pasajero",
        description="Elimina un pasajero del sistema",
        responses={
            204: None,
            404: OpenApiTypes.OBJECT
        }
    )
    def destroy(self, request, pk=None):
        pasajero = PasajeroService.obtener_pasajero(pk)
        if not pasajero:
            return Response({'error': 'Pasajero no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        PasajeroService.eliminar_pasajero(pasajero)
        return Response({'message': 'Pasajero eliminado correctamente.'}, status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Listar reservas de un pasajero",
        description="Obtiene todas las reservas asociadas a un pasajero específico",
        responses={
            200: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        }
    )

    @extend_schema(exclude=True)
    @action(detail=True, methods=['get'])
    def reservas(self, request, pk=None):
        """Lista las reservas asociadas a un pasajero"""
        reservas = PasajeroService.listar_reservas_por_pasajero(pk)
        if reservas is None:
            return Response({'error': 'Pasajero no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        return Response(reservas, status=status.HTTP_200_OK)