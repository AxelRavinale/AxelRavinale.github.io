from django.contrib import admin
from core.models import Localidad, Genero, TipoDocumento, Persona, Provincia, Pais, TipoVuelo, Estado


@admin.register(Pais)
class PaisAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)

@admin.register(Provincia)
class ProvinciaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'pais', 'activo')
    list_filter = ('activo', 'pais')
    search_fields = ('nombre',)

@admin.register(Localidad)
class LocalidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'provincia', 'activo')
    list_filter = ('activo', 'provincia')
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


@admin.register(TipoVuelo)
class TipoVueloAdmin(admin.ModelAdmin):
    list_display = ('name', 'activo')
    list_filter = ('activo',)
    search_fields = ('name',)

@admin.register(Estado)
class EstadoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
