from .models import Pasajero
from .repositories import PasajeroRepository

class PasajeroService:

    @staticmethod
    def listar_pasajeros():
        return PasajeroRepository.listar_todos()

    @staticmethod
    def obtener_pasajero(pk):
        return PasajeroRepository.obtener_por_id(pk)

    @staticmethod
    def registrar_pasajero(data):
        return PasajeroRepository.crear(data)

    @staticmethod
    def editar_pasajero(pasajero, data):
        return PasajeroRepository.actualizar(pasajero, data)

    @staticmethod
    def eliminar_pasajero(pasajero):
        return PasajeroRepository.eliminar(pasajero)

    @staticmethod
    def listar_reservas_por_pasajero(pasajero_id):
        pasajero = PasajeroRepository.obtener_por_id(pasajero_id)
        if not pasajero:
            return None
        reservas = PasajeroRepository.obtener_reservas(pasajero)
        return [{'id': r.id, 'vuelo': r.vuelo.codigo_vuelo, 'estado': r.estado} for r in reservas]
