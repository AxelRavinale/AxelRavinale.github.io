# views.py
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from .serializers import PersonaSerializer
from .services import PersonaService

class PersonaListCreateAPIView(ListCreateAPIView):
    """
    GET /api/personas -> Lista todas las personas (usuarios autenticados)
    POST /api/personas -> Crea una persona (solo admins)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PersonaSerializer

    def get_queryset(self):
        return PersonaService.list_personas()

    def post(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response({"detail": "No tienes permisos para crear personas."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        persona = PersonaService.create_persona(serializer.validated_data)
        return Response(PersonaSerializer(persona).data, status=status.HTTP_201_CREATED)


class PersonaRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    """
    GET /api/core/personas/<id> -> Detalle
    PUT/PATCH -> Actualiza (solo admins)
    DELETE -> Elimina (solo admins)
    """
    serializer_class = PersonaSerializer
    permission_classes = [IsAdminUser]

    def get_object(self):
        persona_id = self.kwargs.get('pk')
        persona = PersonaService.get_persona(persona_id)
        if not persona:
            from rest_framework.exceptions import NotFound
            raise NotFound("Persona no encontrada")
        return persona

    def put(self, request, *args, **kwargs):
        persona = self.get_object()
        serializer = self.get_serializer(persona, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        persona_actualizada = PersonaService.update_persona(persona.id, serializer.validated_data)
        return Response(PersonaSerializer(persona_actualizada).data)

    def delete(self, request, *args, **kwargs):
        persona = self.get_object()
        PersonaService.delete_persona(persona.id)
        return Response({"detail": "Persona eliminada"}, status=status.HTTP_204_NO_CONTENT)
