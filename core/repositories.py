from .models import Persona

class PersonaRepository:

    @staticmethod
    def list_personas():
        return Persona.objects.filter(activo=True)

    @staticmethod
    def get_persona(persona_id):
        try:
            return Persona.objects.get(id=persona_id, activo=True)
        except Persona.DoesNotExist:
            return None

    @staticmethod
    def create_persona(data):
        return Persona.objects.create(**data)

    @staticmethod
    def update_persona(persona, data):
        for field, value in data.items():
            setattr(persona, field, value)
        persona.save()
        return persona

    @staticmethod
    def delete_persona(persona_id):
        persona = PersonaRepository.get_persona(persona_id)
        if persona:
            persona.activo = False
            persona.save()
            return True
        return False
