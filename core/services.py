from .repositories import PersonaRepository

class PersonaService:

    @staticmethod
    def list_personas():
        return PersonaRepository.list_personas()

    @staticmethod
    def get_persona(persona_id):
        return PersonaRepository.get_persona(persona_id)

    @staticmethod
    def create_persona(data):
        return PersonaRepository.create_persona(data)

    @staticmethod
    def update_persona(persona_id, data):
        persona = PersonaRepository.get_persona(persona_id)
        if persona:
            return PersonaRepository.update_persona(persona, data)
        return None

    @staticmethod
    def delete_persona(persona_id):
        return PersonaRepository.delete_persona(persona_id)
