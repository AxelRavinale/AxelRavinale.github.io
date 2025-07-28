from django.db import models
from django.utils.translation import gettext_lazy as _

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
    nombre = models.CharField(max_length=100, verbose_name=_("Nombre"))
    apellido = models.CharField(max_length=100, verbose_name=_("Apellido"))
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.PROTECT, verbose_name=_("Tipo de Documento"))
    numero_documento = models.CharField(max_length=30, unique=True, verbose_name=_("Número de Documento"))
    fecha_nacimiento = models.DateField(verbose_name=_("Fecha de Nacimiento"))
    email = models.EmailField(unique=True, verbose_name=_("Email"))
    localidad = models.ForeignKey(Localidad, on_delete=models.PROTECT, verbose_name=_("Localidad"))
    genero = models.ForeignKey(Genero, on_delete=models.PROTECT, verbose_name=_("Género"))
    activo = models.BooleanField(default=True, verbose_name=_("Activo"))

    class Meta:
        verbose_name = _("Persona")
        verbose_name_plural = _("Personas")

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.tipo_documento.nombre} {self.numero_documento})"


class TipoVuelo(models.Model):
    name = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Estado(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre
