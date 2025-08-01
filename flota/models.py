from django.db import models

TIPOS_AVION = (
    ('pasajeros', 'Pasajeros'),
    ('carga', 'Carga'),
    ('mixto', 'Mixto'),
)

class Avion(models.Model):
    fabricante = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    capacidad = models.PositiveIntegerField()
    matricula = models.CharField(max_length=50, unique=True)
    tipo = models.CharField(max_length=20, choices=TIPOS_AVION, default='pasajeros')
    autonomia_km = models.PositiveIntegerField(help_text="Autonomía en kilómetros")
    fecha_fabricacion = models.DateField()
    en_mantenimiento = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.fabricante} {self.modelo} ({self.matricula})"


