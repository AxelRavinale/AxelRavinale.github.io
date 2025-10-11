from .repositories import TrabajadorRepository

class TrabajadorService:
    @staticmethod
    def listar_trabajadores():
        return TrabajadorRepository.listar()

    @staticmethod
    def obtener_trabajador(trabajador_id):
        return TrabajadorRepository.obtener_por_id(trabajador_id)

    @staticmethod
    def registrar_trabajador(datos):
        return TrabajadorRepository.crear(datos)

    @staticmethod
    def actualizar_trabajador(trabajador_id, datos):
        trabajador = TrabajadorRepository.obtener_por_id(trabajador_id)
        return TrabajadorRepository.actualizar(trabajador, datos)

    @staticmethod
    def eliminar_trabajador(trabajador_id):
        trabajador = TrabajadorRepository.obtener_por_id(trabajador_id)
        return TrabajadorRepository.desactivar(trabajador)
