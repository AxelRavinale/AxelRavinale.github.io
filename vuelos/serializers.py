from rest_framework import serializers
from aviones.models import Avion
from vuelos.models import Vuelo, Escala, TripulacionVuelo
from core.models import Localidad
from .constant import ROLES_TRIPULACION

class LocalidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Localidad
        fields = ['id', 'nombre', 'activo']


class AvionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Avion
        fields = ['id', 'num_avion', 'modelo', 'filas', 'columnas', 'estado', 'km_recorridos', 'activo']


class EscalaSerializer(serializers.ModelSerializer):
    origen = LocalidadSerializer(read_only=True)
    destino = LocalidadSerializer(read_only=True)
    origen_id = serializers.PrimaryKeyRelatedField(queryset=Localidad.objects.all(), source='origen', write_only=True)
    destino_id = serializers.PrimaryKeyRelatedField(queryset=Localidad.objects.all(), source='destino', write_only=True)

    class Meta:
        model = Escala
        fields = [
            'id', 'origen', 'destino', 'origen_id', 'destino_id',
            'fecha_salida', 'fecha_llegada', 'km_estimados', 'activo'
        ]


class VueloSerializer(serializers.ModelSerializer):
    escala = EscalaSerializer(read_only=True)
    escala_id = serializers.PrimaryKeyRelatedField(queryset=Escala.objects.all(), source='escala', write_only=True)
    avion = AvionSerializer(read_only=True)
    avion_id = serializers.PrimaryKeyRelatedField(queryset=Avion.objects.all(), source='avion', write_only=True)

    class Meta:
        model = Vuelo
        fields = ['id', 'codigo_vuelo', 'escala', 'escala_id', 'avion', 'avion_id', 'activo']


class TripulacionVueloSerializer(serializers.ModelSerializer):
    persona_id = serializers.IntegerField()
    vuelo_id = serializers.PrimaryKeyRelatedField(queryset=Vuelo.objects.all(), source='vuelo')
    rol = serializers.ChoiceField(choices=ROLES_TRIPULACION)

    class Meta:
        model = TripulacionVuelo
        fields = ['id', 'vuelo_id', 'persona_id', 'rol']
