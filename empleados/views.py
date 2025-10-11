from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework import status
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

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        trabajador = TrabajadorService.actualizar_trabajador(instance.id, serializer.validated_data)
        return Response(TrabajadorSerializer(trabajador).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        TrabajadorService.eliminar_trabajador(instance.id)
        return Response(status=status.HTTP_204_NO_CONTENT)
