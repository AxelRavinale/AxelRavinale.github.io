from .models import Trabajador
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

class TrabajadorRepository:
    @staticmethod
    def listar():
        return Trabajador.objects.filter(activo=True)

    @staticmethod
    def obtener_por_id(trabajador_id):
        return get_object_or_404(Trabajador, id=trabajador_id)

    @staticmethod
    def crear(datos):
        return Trabajador.objects.create(**datos)

    @staticmethod
    def actualizar(trabajador, datos):
        for attr, value in datos.items():
            setattr(trabajador, attr, value)
        trabajador.save()
        return trabajador

    @staticmethod
    def desactivar(trabajador):
        trabajador.activo = False
        trabajador.save()
        return trabajador
