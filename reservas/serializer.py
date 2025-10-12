from rest_framework import serializers
from .models import Reserva, ReservaDetalle
from vuelos.models import Vuelo
from aviones.models import Asiento


class ReservaDetalleSerializer(serializers.ModelSerializer):
    asiento_numero = serializers.CharField(source="asiento.numero", read_only=True)

    class Meta:
        model = ReservaDetalle
        fields = ["id", "asiento", "asiento_numero", "precio", "estado"]


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
            "estado",
            "monto_total",
            "detalles",
        ]


class CrearReservaSerializer(serializers.Serializer):
    pasajero_id = serializers.IntegerField()
    vuelo_id = serializers.IntegerField()
    asientos = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
