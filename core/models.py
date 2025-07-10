from django.db import models

class Pais(models.Model):
    nombre = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Provincia(models.Model):
    pais = models.ForeignKey(Pais, on_delete=models.CASCADE, related_name='provincias')
    nombre = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']
        constraints = [
            models.UniqueConstraint(fields=['pais', 'nombre'], name='unique_provincia_por_pais')
        ]

    def __str__(self):
        return f"{self.nombre} ({self.pais.nombre})"

class Localidad(models.Model):
    provincia = models.ForeignKey(Provincia, on_delete=models.CASCADE, related_name='localidades', null=True)
    nombre = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']
        constraints = [
            models.UniqueConstraint(fields=['provincia', 'nombre'], name='unique_localidad_por_provincia')
        ]

    def __str__(self):
        return self.nombre


class Genero(models.Model):
    nombre = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class TipoDocumento(models.Model):
    nombre = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

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

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.tipo_documento.nombre} {self.numero_documento})"