from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Persona, Pais, Provincia, Localidad, Genero, TipoDocumento, TipoVuelo, Estado


class PaisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pais
        fields = '__all__'


class ProvinciaSerializer(serializers.ModelSerializer):
    pais = PaisSerializer(read_only=True)
    pais_id = serializers.PrimaryKeyRelatedField(
        queryset=Pais.objects.all(),
        source='pais',
        write_only=True,
        required=False
    )

    class Meta:
        model = Provincia
        fields = '__all__'


class LocalidadSerializer(serializers.ModelSerializer):
    provincia = ProvinciaSerializer(read_only=True)
    provincia_id = serializers.PrimaryKeyRelatedField(
        queryset=Provincia.objects.all(),
        source='provincia',
        write_only=True,
        required=False
    )

    class Meta:
        model = Localidad
        fields = '__all__'


class GeneroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genero
        fields = '__all__'


class TipoDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoDocumento
        fields = '__all__'


class TipoVueloSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoVuelo
        fields = '__all__'


class EstadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estado
        fields = '__all__'


class PersonaSerializer(serializers.ModelSerializer):
    # Para crear usuario junto con persona (opcional)
    username = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    # Hacer el campo user opcional
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Persona
        fields = '__all__'
        extra_kwargs = {
            'user': {'required': False, 'allow_null': True}
        }

    def create(self, validated_data):
        username = validated_data.pop('username', None)
        password = validated_data.pop('password', None)
        
        # Si se proporcionan username y password, crear el usuario
        if username and password:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=validated_data.get('email', ''),
                first_name=validated_data.get('nombre', ''),
                last_name=validated_data.get('apellido', '')
            )
            validated_data['user'] = user
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Remover campos de usuario si vienen en el update
        validated_data.pop('username', None)
        validated_data.pop('password', None)
        
        return super().update(instance, validated_data)


class PersonaSerializer(serializers.ModelSerializer):
    # Para crear usuario junto con persona (opcional)
    username = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    # Hacer el campo user opcional y read_only en updates
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Persona
        fields = '__all__'
        extra_kwargs = {
            'user': {'required': False, 'allow_null': True}
        }

    def create(self, validated_data):
        username = validated_data.pop('username', None)
        password = validated_data.pop('password', None)
        
        # Si se proporcionan username y password, crear el usuario
        if username and password:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=validated_data.get('email', ''),
                first_name=validated_data.get('nombre', ''),
                last_name=validated_data.get('apellido', '')
            )
            validated_data['user'] = user
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # ✅ CORRECCIÓN: Remover campos que no deben actualizarse
        validated_data.pop('username', None)
        validated_data.pop('password', None)
        validated_data.pop('user', None)  # ✅ No permitir cambiar el usuario en updates
        
        return super().update(instance, validated_data)