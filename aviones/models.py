from django.db import models

class Avion(models.Model):
    num_avion = models.CharField(max_length=20, unique=True)
    modelo = models.CharField(max_length=50)
    filas = models.PositiveIntegerField()
    columnas = models.PositiveIntegerField()
    estado = models.CharField(max_length=50)  # Ej: operativo, mantenimiento
    km_recorridos = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.num_avion} ({self.modelo})"

