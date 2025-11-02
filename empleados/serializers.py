from rest_framework import serializers
from .models import Trabajador
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class TrabajadorSerializer(serializers.ModelSerializer):
    usuario = UserSerializer()

    class Meta:
        model = Trabajador
        fields = ['id', 'usuario', 'dni', 'cargo', 'telefono', 'fecha_ingreso', 'activo']

    def create(self, validated_data):
        usuario_data = validated_data.pop('usuario')
        usuario = User.objects.create(**usuario_data)
        return Trabajador.objects.create(usuario=usuario, **validated_data)

    def update(self, instance, validated_data):
        usuario_data = validated_data.pop('usuario', None)
        if usuario_data:
            for attr, value in usuario_data.items():
                setattr(instance.usuario, attr, value)
            instance.usuario.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
