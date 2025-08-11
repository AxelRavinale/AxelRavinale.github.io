from uuid import uuid4
from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from aviones.models import Avion, Asiento
from vuelos.models import Vuelo

User = get_user_model()

class Reserva(models.Model):
    pasajero = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reservas',
        verbose_name=_("Pasajero")
    )
    vuelo = models.ForeignKey(
        Vuelo,
        on_delete=models.CASCADE,
        related_name='reservas',
        verbose_name=_("Vuelo")
    )
    fecha_reserva = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Reserva"))
    precio_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Precio Total")
    )
    codigo_reserva = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        verbose_name=_("Código de Reserva")
    )

    class EstadoReserva(models.TextChoices):
        CREADA = 'CRE', _('Creada')
        CONFIRMADA = 'CON', _('Confirmada')
        CANCELADA = 'CAN', _('Cancelada')

    estado = models.CharField(
        max_length=3,
        choices=EstadoReserva.choices,
        default=EstadoReserva.CREADA,
        verbose_name=_("Estado")
    )
    activo = models.BooleanField(default=True, verbose_name=_("Activo"))

    class Meta:
        verbose_name = _("Reserva")
        verbose_name_plural = _("Reservas")
        ordering = ['-fecha_reserva']

    def __str__(self):
        return f"Reserva {self.codigo_reserva} - {self.pasajero} - {self.vuelo.codigo_vuelo}"

    def save(self, *args, **kwargs):
        if not self.codigo_reserva:
            self.codigo_reserva = uuid4().hex.upper()
        super().save(*args, **kwargs)

    @transaction.atomic
    def actualizar_precio_total(self):
        total = self.detalles.aggregate(
            total=models.Sum('precio')
        )['total'] or 0
        self.precio_total = total
        self.save(update_fields=['precio_total'])

    @transaction.atomic
    def confirmar(self):
        self.estado = self.EstadoReserva.CONFIRMADA
        self.save(update_fields=['estado'])


class ReservaDetalle(models.Model):
    reserva = models.ForeignKey(
        Reserva,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name=_("Reserva")
    )
    asiento = models.ForeignKey(
        Asiento,
        on_delete=models.PROTECT,
        verbose_name=_("Asiento")
    )
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Precio")
    )

    class Meta:
        verbose_name = _("Detalle de Reserva")
        verbose_name_plural = _("Detalles de Reservas")
        unique_together = ('reserva', 'asiento')

    def __str__(self):
        return f"Asiento {self.asiento} en reserva {self.reserva.codigo_reserva}"

    def clean(self):
        # Validar que el asiento pertenece al avión asignado al vuelo principal
        avion_asignado = self.reserva.vuelo.avion_asignado
        if self.asiento.avion != avion_asignado:
            raise ValidationError(_("El asiento no pertenece al avión asignado al vuelo."))
        if self.precio <= 0:
            raise ValidationError(_("El precio debe ser mayor a 0."))
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()  # corre validaciones
        super().save(*args, **kwargs)
        self.reserva.actualizar_precio_total()

    def delete(self, *args, **kwargs):
        reserva = self.reserva
        super().delete(*args, **kwargs)
        reserva.actualizar_precio_total()
