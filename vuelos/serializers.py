from rest_framework import serializers
from .models import Vuelo, Escala, Avion, TripulacionVuelo

class EscalaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Escala
        fields = ['id', 'origen', 'destino', 'km_estimados', 'activo']


class AvionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Avion
        fields = ['id', 'modelo', 'activo']


class TripulacionVueloSerializer(serializers.ModelSerializer):
    persona_nombre = serializers.CharField(source='persona.nombre', read_only=True)

    class Meta:
        model = TripulacionVuelo
        fields = ['id', 'vuelo', 'persona', 'rol', 'persona_nombre']


class VueloSerializer(serializers.ModelSerializer):
    escalas = EscalaSerializer(many=True, read_only=True, source='escalas_vuelo')
    tripulacion = TripulacionVueloSerializer(many=True, read_only=True, source='tripulacion_vuelo')
    avion_detalle = AvionSerializer(source='avion', read_only=True)

    class Meta:
            model = Vuelo
            fields = [
                'id',
                'codigo_vuelo',
                'origen_principal',
                'destino_principal',
                'fecha_salida_estimada',
                'fecha_llegada_estimada',
                'km_totales',
                'avion_asignado',
                'tiene_escalas',
                'activo',
                'cargado_por',
                'fecha_carga',
                'avion_detalle',
                'tripulacion',
                'escalas'  
            ]