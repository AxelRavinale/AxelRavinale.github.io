from .repositories import AvionRepository

class AvionService:

    @staticmethod
    def listar_aviones():
        return AvionRepository.listar_todos()

    @staticmethod
    def obtener_avion(pk):
        return AvionRepository.obtener_por_id(pk)

    @staticmethod
    def registrar_avion(data):
        return AvionRepository.crear(data)

    @staticmethod
    def actualizar_avion(pk, data):
        avion = AvionRepository.obtener_por_id(pk)
        if not avion:
            return None
        return AvionRepository.actualizar(avion, data)

    @staticmethod
    def eliminar_avion(pk):
        avion = AvionRepository.obtener_por_id(pk)
        if not avion:
            return False
        AvionRepository.eliminar(avion)
        return True
