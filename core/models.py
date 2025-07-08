from django.db import models

# Localidad
class Localidad(models.Model):
    nombre = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)


class Genero(models.Model):
    nombre = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

class TipoDocumento(models.Model):
    nombre = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

class Persona(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.PROTECT)
    numero_documento = models.CharField(max_length=30, unique=True)
    fecha_nacimiento = models.DateField()
    email = models.EmailField(unique=True)
    localidad = models.ForeignKey(Localidad, on_delete=models.PROTECT)
    genero = models.ForeignKey(Genero, on_delete=models.PROTECT)
    activo = models.BooleanField(default=True)