from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from .serializers import TrabajadorSerializer
from .services import TrabajadorService

class TrabajadorListCreateAPIView(ListCreateAPIView):
    """
    GET /api/trabajadores/
    POST /api/trabajadores/
    """
    serializer_class = TrabajadorSerializer

    def get_queryset(self):
        return TrabajadorService.listar_trabajadores()

    @extend_schema(
        summary="Listar todos los trabajadores",
        description="Obtiene una lista de todos los trabajadores registrados",
        responses={200: TrabajadorSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Crear un nuevo trabajador",
        description="Registra un nuevo trabajador en el sistema",
        request=TrabajadorSerializer,
        responses={
            201: TrabajadorSerializer,
            400: OpenApiTypes.OBJECT
        }
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        trabajador = TrabajadorService.registrar_trabajador(serializer.validated_data)
        return Response(
            TrabajadorSerializer(trabajador).data,
            status=status.HTTP_201_CREATED
        )


class TrabajadorRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    """
    GET /api/trabajadores/<pk>/
    PUT /api/trabajadores/<pk>/
    DELETE /api/trabajadores/<pk>/
    """
    serializer_class = TrabajadorSerializer

    def get_object(self):
        return TrabajadorService.obtener_trabajador(self.kwargs['pk'])

    @extend_schema(
        summary="Obtener un trabajador específico",
        description="Obtiene los detalles de un trabajador por su ID",
        responses={
            200: TrabajadorSerializer,
            404: OpenApiTypes.OBJECT
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Actualizar un trabajador",
        description="Actualiza los datos de un trabajador existente (actualización parcial permitida)",
        request=TrabajadorSerializer,
        responses={
            200: TrabajadorSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        }
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        trabajador = TrabajadorService.actualizar_trabajador(instance.id, serializer.validated_data)
        return Response(TrabajadorSerializer(trabajador).data)

    @extend_schema(
        summary="Actualización parcial de trabajador",
        description="Actualiza parcialmente los datos de un trabajador",
        request=TrabajadorSerializer,
        responses={
            200: TrabajadorSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @extend_schema(
        summary="Eliminar un trabajador",
        description="Elimina un trabajador del sistema",
        responses={
            204: None,
            404: OpenApiTypes.OBJECT
        }
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        TrabajadorService.eliminar_trabajador(instance.id)
        return Response(status=status.HTTP_204_NO_CONTENT)