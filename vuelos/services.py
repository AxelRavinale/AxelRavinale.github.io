from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Vuelo, EscalaVuelo, TripulacionVuelo

class VueloService:
    @staticmethod
    def crear_vuelo(data, user):
        vuelo = Vuelo.objects.create(
            codigo_vuelo=data.get('codigo_vuelo'),
            avion=data.get('avion'),
            origen=data.get('origen'),
            destino=data.get('destino'),
            fecha_salida=data.get('fecha_salida'),
            fecha_llegada=data.get('fecha_llegada'),
            tiene_escalas=data.get('tiene_escalas', False),
            cargado_por=user
        )
        return vuelo

    @staticmethod
    def actualizar_vuelo(vuelo, data):
        for attr, value in data.items():
            setattr(vuelo, attr, value)
        vuelo.save()
        return vuelo

    @staticmethod
    def eliminar_vuelo(vuelo):
        vuelo.activo = False
        vuelo.save()
        return vuelo

    @staticmethod
    def validar_fechas(fecha_salida, fecha_llegada):
        if fecha_llegada <= fecha_salida:
            raise ValidationError("La fecha de llegada debe ser posterior a la de salida.")

    @staticmethod
    def obtener_detalle_completo(vuelo):
        return {
            "vuelo": vuelo,
            "escalas": vuelo.escalas_vuelo.all(),
            "tripulacion": vuelo.tripulacion_vuelo.all(),
        }
