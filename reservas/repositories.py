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
    def obtener_reservas_vuelo(vuelo_id):
        """Obtiene todas las reservas de un vuelo específico"""
        return Reserva.objects.filter(
            vuelo_id=vuelo_id,
            activo=True
        ).select_related('vuelo', 'pasajero').prefetch_related('detalles')

    @staticmethod
    @transaction.atomic
    def crear_reserva(pasajero, vuelo, asientos_vuelo, precio_total):
        """
        Crea una reserva con asientos de vuelo
        asientos_vuelo: lista de objetos AsientoVuelo
        """
        reserva = Reserva.objects.create(
            pasajero=pasajero,
            vuelo=vuelo,
            precio_total=precio_total,
            estado=Reserva.EstadoChoices.CREADA  # ✅ Usar el enum
        )

        for asiento_vuelo in asientos_vuelo:
            ReservaDetalle.objects.create(
                reserva=reserva,
                asiento_vuelo=asiento_vuelo,
                precio_pagado=asiento_vuelo.precio,  # ✅ El precio viene del AsientoVuelo
            )

        # Recalcular precio total
        reserva.calcular_precio_total()
        
        return reserva

    @staticmethod
    def actualizar_estado(reserva, nuevo_estado):
        reserva.estado = nuevo_estado
        reserva.save()
        return reserva