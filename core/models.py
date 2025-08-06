from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

class Pais(models.Model):
    nombre = models.CharField(max_length=100, verbose_name=_("Nombre"))
    activo = models.BooleanField(default=True, verbose_name=_("Activo"))

    class Meta:
        ordering = ['nombre']
        verbose_name = _("País")
        verbose_name_plural = _("Países")

    def __str__(self):
        return self.nombre


class Provincia(models.Model):
    pais = models.ForeignKey(Pais, on_delete=models.CASCADE, related_name='provincias', verbose_name=_("País"))
    nombre = models.CharField(max_length=100, verbose_name=_("Nombre"))
    activo = models.BooleanField(default=True, verbose_name=_("Activo"))

    class Meta:
        ordering = ['nombre']
        verbose_name = _("Provincia")
        verbose_name_plural = _("Provincias")
        constraints = [
            models.UniqueConstraint(fields=['pais', 'nombre'], name='unique_provincia_por_pais')
        ]

    def __str__(self):
        return f"{self.nombre} ({self.pais.nombre})"

class Localidad(models.Model):
    provincia = models.ForeignKey(Provincia, on_delete=models.CASCADE, related_name='localidades', null=True, verbose_name=_("Provincia"))
    nombre = models.CharField(max_length=100, verbose_name=_("Nombre"))
    activo = models.BooleanField(default=True, verbose_name=_("Activo"))

    class Meta:
        ordering = ['nombre']
        verbose_name = _("Localidad")
        verbose_name_plural = _("Localidades")
        constraints = [
            models.UniqueConstraint(fields=['provincia', 'nombre'], name='unique_localidad_por_provincia')
        ]

    def __str__(self):
        return self.nombre


class Genero(models.Model):
    nombre = models.CharField(max_length=100, verbose_name=_("Nombre"))
    activo = models.BooleanField(default=True, verbose_name=_("Activo"))

    class Meta:
        verbose_name = _("Género")
        verbose_name_plural = _("Géneros")

    def __str__(self):
        return self.nombre


class TipoDocumento(models.Model):
    nombre = models.CharField(max_length=100, verbose_name=_("Nombre"))
    activo = models.BooleanField(default=True, verbose_name=_("Activo"))

    class Meta:
        verbose_name = _("Tipo de Documento")
        verbose_name_plural = _("Tipos de Documento")

    def __str__(self):
        return self.nombre



class Persona(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Usuario"))
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    tipo_documento = models.CharField(max_length=20)
    numero_documento = models.CharField(max_length=20)
    fecha_nacimiento = models.DateField()
    localidad = models.CharField(max_length=100)
    email = models.EmailField()
    activo = models.BooleanField(default=True)
    genero = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    

class TipoVuelo(models.Model):
    name = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Estado(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre
