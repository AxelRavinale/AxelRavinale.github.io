from django.db import models

# Localidad
class Localidad(models.Model):
    nombre = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)
