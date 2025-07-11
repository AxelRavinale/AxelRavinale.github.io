from django.contrib import admin
from aviones.models import Avion, Asiento

class AvionAdmin(admin.ModelAdmin):
    list_display = ('num_avion', 'modelo', 'estado', 'filas', 'columnas')
    
    def save_model(self, request, obj, form, change):
        nuevo_avion = not obj.pk
        super().save_model(request, obj, form, change)
        if nuevo_avion:
            obj.generar_asientos()

admin.site.register(Avion, AvionAdmin)
admin.site.register(Asiento)
