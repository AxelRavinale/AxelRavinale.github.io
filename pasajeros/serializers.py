from rest_framework import serializers
from .models import Pasajero

class PasajeroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pasajero
        fields = ['id', 'nombre', 'apellido', 'dni', 'email', 'telefono', 'fecha_registro', 'activo']
