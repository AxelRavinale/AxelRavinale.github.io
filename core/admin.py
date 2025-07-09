# core/admin.py
from django.contrib import admin
from core.models import Localidad, Genero, TipoDocumento, Persona

@admin.register(Localidad)
class LocalidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)

@admin.register(Genero)
class GeneroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)

@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)

@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'tipo_documento', 'numero_documento', 'email', 'localidad', 'genero', 'activo')
    list_filter = ('activo', 'genero', 'localidad')
    search_fields = ('nombre', 'apellido', 'numero_documento', 'email')
