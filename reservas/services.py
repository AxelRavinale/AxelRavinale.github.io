from .repositories import ReservaRepository
from vuelos.models import Vuelo
from pasajeros.models import Pasajero
from aviones.models import Asiento
from django.core.exceptions import ValidationError

class ReservaService:

    @staticmethod
    def listar_reservas():
        return ReservaRepository.obtener_reservas()

    @staticmethod
    def obtener_reserva(reserva_id):
        return ReservaRepository.obtener_por_id(reserva_id)

    @staticmethod
    def crear_reserva(pasajero_id, vuelo_id, asientos_ids):
        pasajero = Pasajero.objects.get(id=pasajero_id)
        vuelo = Vuelo.objects.get(id=vuelo_id)
        asientos = Asiento.objects.filter(id__in=asientos_ids, estado="libre")

        if len(asientos) != len(asientos_ids):
            raise ValidationError("Uno o más asientos ya están ocupados.")

        precio_total = vuelo.precio_base * len(asientos)

        return ReservaRepository.crear_reserva(pasajero, vuelo, asientos, precio_total)

    @staticmethod
    def cambiar_estado(reserva_id, nuevo_estado):
        reserva = ReservaRepository.obtener_por_id(reserva_id)
        return ReservaRepository.actualizar_estado(reserva, nuevo_estado)
