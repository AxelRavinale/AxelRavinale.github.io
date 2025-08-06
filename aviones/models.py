from django.db import models
from django.utils.translation import gettext_lazy as _

class Avion(models.Model):
    num_avion = models.CharField(max_length=20, unique=True, verbose_name=_("Número de Avión"))
    modelo = models.CharField(max_length=50, verbose_name=_("Modelo"))
    filas = models.PositiveIntegerField(verbose_name=_("Filas"))
    columnas = models.PositiveIntegerField(verbose_name=_("Columnas"))
    estado = models.CharField(max_length=50, verbose_name=_("Estado"), 
                             help_text=_("Ej: operativo, mantenimiento"))
    km_recorridos = models.PositiveIntegerField(default=0, verbose_name=_("Kilómetros Recorridos"))
    activo = models.BooleanField(default=True, verbose_name=_("Activo"))

    class Meta:
        verbose_name = _("Avión")
        verbose_name_plural = _("Aviones")
        ordering = ['num_avion']

    def __str__(self):
        return f"{self.num_avion} ({self.modelo})"

    def generar_asientos(self):
        """
        Método para generar automáticamente los asientos del avión
        según las filas y columnas.
        """
        columnas = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'  # Soporta hasta 26 columnas
        for fila in range(1, self.filas + 1):
            for col in range(self.columnas):
                Asiento.objects.create(
                    avion=self,
                    fila=fila,
                    columna=columnas[col],
                    estado='libre'
                )


class Asiento(models.Model):
    ESTADOS = (
        ('libre', _('Libre')),
        ('reservado', _('Reservado')),
        ('ocupado', _('Ocupado')),
    )

    avion = models.ForeignKey(Avion, on_delete=models.CASCADE, related_name='asientos', 
                             verbose_name=_("Avión"))
    fila = models.PositiveIntegerField(verbose_name=_("Fila"))
    columna = models.CharField(max_length=2, verbose_name=_("Columna"))
    estado = models.CharField(max_length=10, choices=ESTADOS, default='libre', 
                             verbose_name=_("Estado"))

    class Meta:
        verbose_name = _("Asiento")
        verbose_name_plural = _("Asientos")
        ordering = ['avion', 'fila', 'columna']
        unique_together = ['avion', 'fila', 'columna']

    def __str__(self):
        return f"Asiento {self.fila}{self.columna} - {self.avion.num_avion}"