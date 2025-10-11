from rest_framework import serializers
from .models import Persona, Pais, Provincia, Localidad, Genero, TipoDocumento, TipoVuelo, Estado


class PaisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pais
        fields = '__all__'


class ProvinciaSerializer(serializers.ModelSerializer):
    pais = PaisSerializer(read_only=True)

    class Meta:
        model = Provincia
        fields = '__all__'


class LocalidadSerializer(serializers.ModelSerializer):
    provincia = ProvinciaSerializer(read_only=True)

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
    class Meta:
        model = Persona
        fields = '__all__'
