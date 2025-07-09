from django.contrib import admin
from vuelos.models import Vuelo, Escala, TripulacionVuelo
from aviones.models import Avion
from core.models import Localidad

@admin.register(Vuelo)
class VueloAdmin(admin.ModelAdmin):
    list_display = ('codigo_vuelo', 'escala', 'avion', 'activo')
    list_filter = ('activo', 'avion')
    search_fields = ('codigo_vuelo',)


@admin.register(Escala)
class EscalaAdmin(admin.ModelAdmin):
    list_display = ('origen', 'destino', 'fecha_salida', 'fecha_llegada', 'km_estimados', 'activo')
    list_filter = ('activo', 'origen', 'destino')
    search_fields = ('origen__nombre', 'destino__nombre')  # Ajustá si tenés campo 'nombre'


@admin.register(TripulacionVuelo)
class TripulacionVueloAdmin(admin.ModelAdmin):
    list_display = ('vuelo', 'persona', 'rol')
    list_filter = ('rol',)
    search_fields = ('persona__nombre', 'vuelo__codigo_vuelo')
