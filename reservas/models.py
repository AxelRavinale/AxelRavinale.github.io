from django.db import models
from django.contrib.auth.models import User
from vuelos.models import Vuelo
from core.models import TipoVuelo, Estado 

class Reserva(models.Model):
    pasajero = models.ForeignKey(User, on_delete=models.CASCADE)
    vuelo = models.ForeignKey(Vuelo, on_delete=models.CASCADE)
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    
    fila = models.IntegerField()
    columna = models.IntegerField()
    
    tipo_vuelo = models.ForeignKey(TipoVuelo, on_delete=models.SET_NULL, null=True)
    estado_pedido = models.ForeignKey(Estado, on_delete=models.SET_NULL, null=True)
    
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.pasajero.username} → {self.vuelo.codigo_vuelo} (F:{self.fila} C:{self.columna})"
