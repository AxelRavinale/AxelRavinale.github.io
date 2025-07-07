from django.db import models
from aviones.models import Avion
from core.models import Localidad


class Escala(models.Model):
    origen = models.ForeignKey(Localidad, related_name='escalas_origen', on_delete=models.CASCADE)
    destino = models.ForeignKey(Localidad, related_name='escalas_destino', on_delete=models.CASCADE)
    fecha_salida = models.DateTimeField()
    fecha_llegada = models.DateTimeField()
    km_estimados = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.origen} → {self.destino}"



class Vuelo(models.Model):
    escala = models.ForeignKey(Escala, related_name='vuelos', on_delete=models.CASCADE)
    avion = models.ForeignKey(Avion, on_delete=models.CASCADE)
    codigo_vuelo = models.CharField(max_length=20, unique=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"Vuelo {self.codigo_vuelo} ({self.escala})"


class TripulacionVuelo(models.Model):
    ROLES = [
        ('piloto', 'Piloto'),
        ('copiloto', 'Copiloto'),
        ('asistente', 'Asistente de vuelo'),
    ]

    vuelo = models.ForeignKey(Vuelo, related_name='tripulacion', on_delete=models.CASCADE)
    persona = models.ForeignKey('personas.Persona', on_delete=models.CASCADE)
    rol = models.CharField(max_length=20, choices=ROLES)

    def __str__(self):
        return f"{self.rol} en {self.vuelo.codigo_vuelo} - {self.persona}"

