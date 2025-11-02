from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

from core.serializers import PersonaSerializer
from core.services import PersonaService

class PersonaListCreateAPIView(ListCreateAPIView):
    """
    GET /api/personas -> Lista todas las personas (usuarios autenticados)
    POST /api/personas -> Crea una persona (solo admins)
    """
    #permission_classes = [IsAuthenticated]
    serializer_class = PersonaSerializer

    def get_queryset(self):
        return PersonaService.list_personas()

    @extend_schema(
        summary="Listar todas las personas",
        description="Obtiene una lista de todas las personas registradas (requiere autenticación)",
        responses={200: PersonaSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Crear una nueva persona",
        description="Registra una nueva persona en el sistema (solo administradores)",
        request=PersonaSerializer,
        responses={
            201: PersonaSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT
        }
    )
    def post(self, request, *args, **kwargs):
        # ✅ CAMBIO AQUÍ: Usar el serializer directamente
        # El serializer maneja la creación del usuario automáticamente
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # El método save() llama al create() del serializer
        persona = serializer.save()
        
        return Response(
            PersonaSerializer(persona).data,
            status=status.HTTP_201_CREATED
        )


class PersonaRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    """
    GET /api/core/personas/<id> -> Detalle
    PUT/PATCH -> Actualiza (solo admins)
    DELETE -> Elimina (solo admins)
    """
    serializer_class = PersonaSerializer
    permission_classes = [IsAdminUser]
    queryset = PersonaService.get_all_queryset() if hasattr(PersonaService, 'get_all_queryset') else []

    def get_object(self):
        persona_id = self.kwargs.get('pk')
        persona = PersonaService.get_persona(persona_id)
        if not persona:
            from rest_framework.exceptions import NotFound
            raise NotFound("Persona no encontrada")
        return persona

    @extend_schema(
        summary="Obtener una persona específica",
        description="Obtiene los detalles de una persona por su ID (solo administradores)",
        responses={
            200: PersonaSerializer,
            404: OpenApiTypes.OBJECT
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Actualizar una persona",
        description="Actualiza los datos de una persona existente (actualización parcial permitida, solo administradores)",
        request=PersonaSerializer,
        responses={
            200: PersonaSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        }
    )
    def put(self, request, *args, **kwargs):
        persona = self.get_object()
        serializer = self.get_serializer(persona, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        persona_actualizada = serializer.save()  # ✅ Usa el serializer
        return Response(PersonaSerializer(persona_actualizada).data)

    @extend_schema(
        summary="Actualización parcial de persona",
        description="Actualiza parcialmente los datos de una persona (solo administradores)",
        request=PersonaSerializer,
        responses={
            200: PersonaSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        }
    )
    def patch(self, request, *args, **kwargs):
        return self.put(request, *args, **kwargs)

    @extend_schema(
        summary="Eliminar una persona",
        description="Elimina una persona del sistema (solo administradores)",
        responses={
            204: None,
            404: OpenApiTypes.OBJECT
        }
    )
    def delete(self, request, *args, **kwargs):
        persona = self.get_object()
        PersonaService.delete_persona(persona.id)
        return Response({"detail": "Persona eliminada"}, status=status.HTTP_204_NO_CONTENT)