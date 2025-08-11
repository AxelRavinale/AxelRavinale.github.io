from django.contrib import admin
from .models import Reserva

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = [
        'pasajero',
        'vuelo',
        'fecha_reserva',
        'get_fila',
        'get_columna',
        'get_tipo_vuelo',
    ]
    list_filter = ['vuelo', 'estado', 'activo']

    def get_fila(self, obj):
        return obj.asiento.fila  # Asumiendo que Asiento tiene atributo fila
    get_fila.short_description = 'Fila'
    get_fila.admin_order_field = 'asiento__fila'

    def get_columna(self, obj):
        return obj.asiento.columna  # Asumiendo que Asiento tiene atributo columna
    get_columna.short_description = 'Columna'
    get_columna.admin_order_field = 'asiento__columna'

    def get_tipo_vuelo(self, obj):
        return obj.vuelo.tipo_vuelo.nombre  # Ajusta según tu relación real
    get_tipo_vuelo.short_description = 'Tipo de Vuelo'
    get_tipo_vuelo.admin_order_field = 'vuelo__tipo_vuelo__nombre'
