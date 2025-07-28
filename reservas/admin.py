from django.contrib import admin
from reservas.models import Reserva

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = (
        'pasajero',
        'vuelo',
        'fecha_reserva',
        'fila',
        'columna',
        'tipo_vuelo',
        'estado_pedido',
        'activo'
    )
    list_filter = ('activo', 'tipo_vuelo', 'estado_pedido')
    search_fields = ('pasajero__username', 'vuelo__codigo_vuelo')
    ordering = ('fecha_reserva',)
    
    def has_delete_permission(self, request, obj=None):
        # Disable delete permission for all users
        return False
