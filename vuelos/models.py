from django.db import models
from django.contrib.auth.models import User
from aviones.models import Avion
from core.models import Localidad, Persona
from .constant import ROLES_TRIPULACION


class Escala(models.Model):
    """Modelo para definir escalas independientes que pueden ser reutilizadas"""
    origen = models.ForeignKey(Localidad, related_name='escalas_origen', on_delete=models.CASCADE, null=True, blank=True)
    destino = models.ForeignKey(Localidad, related_name='escalas_destino', on_delete=models.CASCADE, null=True, blank=True)
    km_estimados = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Escala"
        verbose_name_plural = "Escalas"

    def __str__(self):
        return f"{self.origen} → {self.destino}"


class Vuelo(models.Model):
    """Modelo principal para vuelos"""
    codigo_vuelo = models.CharField(max_length=20, unique=True)
    origen_principal = models.ForeignKey(Localidad, related_name='vuelos_origen', on_delete=models.CASCADE, null=True, blank=True)
    destino_principal = models.ForeignKey(Localidad, related_name='vuelos_destino', on_delete=models.CASCADE, null=True, blank=True)
    fecha_salida_estimada = models.DateTimeField()
    fecha_llegada_estimada = models.DateTimeField()
    km_totales = models.PositiveIntegerField(null=True, blank=True)
    avion_asignado = models.ForeignKey(Avion, on_delete=models.SET_NULL, null=True, blank=True)
    activo = models.BooleanField(default=True)
    cargado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_carga = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vuelo"
        verbose_name_plural = "Vuelos"
        ordering = ['fecha_salida_estimada']

    def __str__(self):
        return f"Vuelo {self.codigo_vuelo} de {self.origen_principal} a {self.destino_principal}"

    @property
    def tiene_escalas(self):
        return self.escalas_vuelo.filter(activo=True).exists()

    @property
    def numero_escalas(self):
        return self.escalas_vuelo.filter(activo=True).count()

    @property
    def duracion_total(self):
        return self.fecha_llegada_estimada - self.fecha_salida_estimada

    @property
    def distancia_recorrida(self):
        return sum(e.km_estimados for e in self.escalas_vuelo.filter(activo=True)) or self.km_totales


class EscalaVuelo(models.Model):
    """Modelo para escalas específicas de un vuelo"""
    vuelo = models.ForeignKey(Vuelo, related_name='escalas_vuelo', on_delete=models.CASCADE)
    escala = models.ForeignKey(Escala, related_name='escalas_vuelo', on_delete=models.CASCADE)
    orden = models.PositiveIntegerField(default=1)
    fecha_salida = models.DateTimeField()
    fecha_llegada = models.DateTimeField()
    avion = models.ForeignKey(Avion, on_delete=models.CASCADE)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Escala de Vuelo"
        verbose_name_plural = "Escalas de Vuelo"
        ordering = ['vuelo', 'orden']
        unique_together = ['vuelo', 'orden']

    def __str__(self):
        return f"Escala {self.orden}: {self.origen} → {self.destino} ({self.vuelo.codigo_vuelo})"

    @property
    def origen(self):
        return self.escala.origen

    @property
    def destino(self):
        return self.escala.destino

    @property
    def km_estimados(self):
        return self.escala.km_estimados

    @property
    def duracion_escala(self):
        return self.fecha_llegada - self.fecha_salida


class TripulacionVuelo(models.Model):
    """Modelo para la tripulación de cada vuelo"""
    vuelo = models.ForeignKey(Vuelo, related_name='tripulacion', on_delete=models.CASCADE)
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    rol = models.CharField(max_length=20, choices=ROLES_TRIPULACION)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tripulación de Vuelo"
        verbose_name_plural = "Tripulaciones de Vuelo"
        unique_together = ['vuelo', 'persona', 'rol']

    def __str__(self):
        return f"{self.rol.title()} en {self.vuelo.codigo_vuelo} — {self.persona}"


class TripulacionEscala(models.Model):
    """Modelo para tripulación específica de cada escala (si es diferente)"""
    escala_vuelo = models.ForeignKey(EscalaVuelo, related_name='tripulacion_escala', on_delete=models.CASCADE)
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    rol = models.CharField(max_length=20, choices=ROLES_TRIPULACION)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tripulación de Escala"
        verbose_name_plural = "Tripulaciones de Escala"
        unique_together = ['escala_vuelo', 'persona', 'rol']

    def __str__(self):
        return f"{self.rol.title()} en {self.escala_vuelo} — {self.persona}"
