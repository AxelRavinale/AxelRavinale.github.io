from django.contrib import admin
from vuelos.models import Vuelo, Escala, TripulacionVuelo
from aviones.models import Avion
from core.models import Localidad, Persona, Provincia, Pais

@admin.register(Vuelo)
class VueloAdmin(admin.ModelAdmin):
    list_display = (
        'codigo_vuelo',
        'origen_principal',
        'destino_principal',
        'avion_asignado',
        'numero_escalas',
        'activo',
        'fecha_salida_estimada',
        'fecha_llegada_estimada',
    )
    list_filter = ('activo', 'origen_principal', 'destino_principal', 'avion_asignado')
    search_fields = ('codigo_vuelo',)
    ordering = ('fecha_salida_estimada',)

    @admin.display(description='Escalas')
    def numero_escalas(self, obj):
        return obj.numero_escalas


@admin.register(Escala)
class EscalaAdmin(admin.ModelAdmin):
    list_display = (
        'origen',
        'destino',
        'km_estimados',
        'activo',
    )
    list_filter = ('activo', 'origen', 'destino')
    search_fields = ('origen__nombre', 'destino__nombre') 


@admin.register(TripulacionVuelo)
class TripulacionVueloAdmin(admin.ModelAdmin):
    list_display = ('vuelo', 'persona', 'rol', 'activo')
    list_filter = ('rol', 'activo')
    search_fields = ('persona__nombre', 'vuelo__codigo_vuelo')
    ordering = ('vuelo', 'rol')
