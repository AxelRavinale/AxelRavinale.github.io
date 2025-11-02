from vuelos.models import Vuelo
from reservas.models import Reserva
from pasajeros.models import Pasajero

class ReporteRepository:
    @staticmethod
    def obtener_pasajeros_por_vuelo(vuelo_id):
        try:
            vuelo = Vuelo.objects.get(id=vuelo_id)
        except Vuelo.DoesNotExist:
            return None, None

        pasajeros = Reserva.objects.filter(vuelo=vuelo).select_related('pasajero__persona', 'asiento')
        return vuelo, pasajeros

    @staticmethod
    def obtener_reservas_activas_por_pasajero(pasajero_id):
        try:
            pasajero = Pasajero.objects.get(id=pasajero_id)
        except Pasajero.DoesNotExist:
            return None, None

        reservas = Reserva.objects.filter(pasajero=pasajero, estado__in=['Activa', 'Confirmada']).select_related('vuelo')
        return pasajero, reservas
