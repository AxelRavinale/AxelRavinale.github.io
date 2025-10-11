from django.db import models
from django.contrib.auth.models import User

class Trabajador(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    dni = models.CharField(max_length=10, unique=True)
    cargo = models.CharField(max_length=50)
    telefono = models.CharField(max_length=15)
    fecha_ingreso = models.DateField()
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.cargo}"
