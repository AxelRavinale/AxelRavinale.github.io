from rest_framework import serializers
from .models import Reserva, ReservaDetalle ,Boleto

from vuelos.models import Vuelo
from aviones.models import Asiento


class ReservaDetalleSerializer(serializers.ModelSerializer):
    asiento_numero = serializers.CharField(source="asiento.numero", read_only=True)

    class Meta:
        model = ReservaDetalle
        fields = ["id", "asiento_vuelo", "asiento_numero", "precio_pagado", "fecha_asignacion"]


class ReservaSerializer(serializers.ModelSerializer):
    detalles = ReservaDetalleSerializer(many=True, read_only=True)
    vuelo_info = serializers.CharField(source="vuelo.__str__", read_only=True)

    class Meta:
        model = Reserva
        fields = [
            "id",
            "pasajero",
            "vuelo",
            "vuelo_info",
            "fecha_reserva",
            "codigo_reserva",
            "estado",
            "precio_total",  # ✅ Cambié de monto_total a precio_total
            "fecha_limite_pago",
            "fecha_pago",
            "metodo_pago",
            "detalles",
        ]
        read_only_fields = ["codigo_reserva", "fecha_reserva", "precio_total"]


class CrearReservaSerializer(serializers.Serializer):
    pasajero_id = serializers.IntegerField(
        help_text="ID del pasajero"
    )
    vuelo_id = serializers.IntegerField(
        help_text="ID del vuelo"
    )
    asientos = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="Lista de IDs de asientos de vuelo (AsientoVuelo) a reservar"
    )


class BoletoSerializer(serializers.ModelSerializer):
    reserva_info = serializers.CharField(source="reserva.codigo_reserva", read_only=True)
    vuelo_data = serializers.JSONField(read_only=True)
    asientos_data = serializers.JSONField(read_only=True)
    pasajero_data = serializers.JSONField(read_only=True)

    class Meta:
        model = Boleto  # ✅ CORRECTO - debe ser Boleto, no Reserva
        fields = [
            "id",
            "reserva",
            "reserva_info",
            "codigo_barras",
            "fecha_emision",
            "vuelo_data",
            "asientos_data",
            "pasajero_data",
            "usado",
            "fecha_uso",
            "activo"
        ]
        read_only_fields = ["codigo_barras", "fecha_emision", "activo"]