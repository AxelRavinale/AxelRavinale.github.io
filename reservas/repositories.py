from django.shortcuts import get_object_or_404
from .models import Reserva, ReservaDetalle
from vuelos.models import Vuelo
from aviones.models import Asiento
from pasajeros.models import Pasajero
from django.db import transaction

class ReservaRepository:

    @staticmethod
    def obtener_reservas():
        return Reserva.objects.select_related("vuelo", "pasajero").all()

    @staticmethod
    def obtener_por_id(reserva_id):
        return get_object_or_404(Reserva, id=reserva_id)

    @staticmethod
    @transaction.atomic
    def crear_reserva(pasajero, vuelo, asientos, precio_total):
        reserva = Reserva.objects.create(
            pasajero=pasajero,
            vuelo=vuelo,
            monto_total=precio_total,
            estado="CREADA"
        )

        for asiento in asientos:
            ReservaDetalle.objects.create(
                reserva=reserva,
                asiento=asiento,
                precio=vuelo.precio_base,
                estado="pendiente"
            )
            asiento.estado = "reservado"
            asiento.save()

        return reserva

    @staticmethod
    def actualizar_estado(reserva, nuevo_estado):
        reserva.estado = nuevo_estado
        reserva.save()
        return reserva
