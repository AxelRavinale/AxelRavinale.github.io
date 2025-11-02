from .models import Pasajero 
from reservas.models import Reserva
class PasajeroRepository:

    @staticmethod
    def listar_todos():
        return Pasajero.objects.all()

    @staticmethod
    def obtener_por_id(pk):
        try:
            return Pasajero.objects.get(pk=pk)
        except Pasajero.DoesNotExist:
            return None

    @staticmethod
    def obtener_reservas(pasajero):
        return Reserva.objects.filter(pasajero=pasajero)
    @staticmethod
    def crear(data):
        return Pasajero.objects.create(**data)

    @staticmethod
    def actualizar(pasajero, data):
        for attr, value in data.items():
            setattr(pasajero, attr, value)
        pasajero.save()
        return pasajero

    @staticmethod
    def eliminar(pasajero):
        pasajero.delete()
