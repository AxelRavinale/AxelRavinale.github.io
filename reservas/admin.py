from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.utils import timezone
from datetime import timedelta

from .models import AsientoVuelo, Reserva, ReservaDetalle, Boleto, ConfiguracionVuelo


@admin.register(ConfiguracionVuelo)
class ConfiguracionVueloAdmin(admin.ModelAdmin):
    """Admin para configuraciones de vuelo"""
    list_display = [
        'vuelo_codigo', 'vuelo_origen_destino', 'configurado', 
        'total_asientos_configurados', 'asientos_habilitados',
        'fecha_configuracion', 'configurado_por'
    ]
    list_filter = ['configurado', 'fecha_configuracion']
    search_fields = ['vuelo__codigo_vuelo', 'vuelo__origen_principal__nombre']
    readonly_fields = ['fecha_configuracion']
    
    def vuelo_codigo(self, obj):
        return obj.vuelo.codigo_vuelo
    vuelo_codigo.short_description = 'Código Vuelo'
    
    def vuelo_origen_destino(self, obj):
        origen = obj.vuelo.origen_principal.nombre if obj.vuelo.origen_principal else 'N/A'
        destino = obj.vuelo.destino_principal.nombre if obj.vuelo.destino_principal else 'N/A'
        return f"{origen} → {destino}"
    vuelo_origen_destino.short_description = 'Ruta'


class ReservaDetalleInline(admin.TabularInline):
    """Inline para detalles de reserva"""
    model = ReservaDetalle
    extra = 0
    readonly_fields = ['fecha_asignacion', 'asiento_info', 'precio_pagado']
    fields = ['asiento_vuelo', 'asiento_info', 'precio_pagado', 'fecha_asignacion']
    
    def asiento_info(self, obj):
        if obj.asiento_vuelo and obj.asiento_vuelo.asiento:
            asiento = obj.asiento_vuelo.asiento
            return f"{asiento.numero} ({asiento.avion.modelo})"
        return "N/A"
    asiento_info.short_description = 'Asiento'


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    """Admin principal para reservas"""
    list_display = [
        'codigo_reserva', 'pasajero_info', 'vuelo_info', 'estado_display',
        'precio_total', 'fecha_reserva', 'fecha_limite_pago', 'acciones'
    ]
    list_filter = [
        'estado', 'fecha_reserva', 'vuelo__origen_principal', 
        'vuelo__destino_principal', 'activo'
    ]
    search_fields = [
        'codigo_reserva', 'pasajero__username', 'pasajero__first_name',
        'pasajero__last_name', 'pasajero__email', 'vuelo__codigo_vuelo'
    ]
    readonly_fields = [
        'codigo_reserva', 'fecha_reserva', 'fecha_creacion', 'fecha_modificacion'
    ]
    
    inlines = [ReservaDetalleInline]
    
    # Organizar campos en secciones
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo_reserva', 'pasajero', 'vuelo', 'estado')
        }),
        ('Pagos y Precios', {
            'fields': ('precio_total', 'metodo_pago', 'numero_tarjeta_enmascarado', 
                      'fecha_pago', 'fecha_limite_pago')
        }),
        ('Control', {
            'fields': ('activo',)
        }),
        ('Auditoría', {
            'fields': ('fecha_reserva', 'fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
    
    def pasajero_info(self, obj):
        nombre = obj.pasajero.get_full_name() or obj.pasajero.username
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            nombre, obj.pasajero.email
        )
    pasajero_info.short_description = 'Pasajero'
    
    def vuelo_info(self, obj):
        vuelo = obj.vuelo
        origen = vuelo.origen_principal.nombre if vuelo.origen_principal else 'N/A'
        destino = vuelo.destino_principal.nombre if vuelo.destino_principal else 'N/A'
        fecha = vuelo.fecha_salida_estimada.strftime('%d/%m/%Y') if vuelo.fecha_salida_estimada else 'N/A'
        
        return format_html(
            '<strong>{}</strong><br><small>{} → {}</small><br><small>{}</small>',
            vuelo.codigo_vuelo, origen, destino, fecha
        )
    vuelo_info.short_description = 'Vuelo'
    
    def estado_display(self, obj):
        colores = {
            'CRE': '#17a2b8',  # info
            'RSP': '#ffc107',  # warning
            'CON': '#28a745',  # success
            'CAN': '#dc3545',  # danger
            'EXP': '#6c757d',  # secondary
        }
        color = colores.get(obj.estado, '#6c757d')
        
        # Agregar info adicional según estado
        extra_info = ''
        if obj.estado == 'RSP' and obj.fecha_limite_pago:
            if obj.esta_expirada:
                extra_info = '<br><small style="color: #dc3545;">⚠️ EXPIRADA</small>'
            else:
                horas = obj.horas_para_expiracion
                if horas and horas <= 48:
                    extra_info = f'<br><small style="color: #dc3545;">⏰ {horas}h restantes</small>'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>{}',
            color, obj.get_estado_display(), extra_info
        )
    estado_display.short_description = 'Estado'
    
    def acciones(self, obj):
        acciones = []
        
        # Ver detalles
        url_detail = reverse('admin:reservas_reserva_change', args=[obj.pk])
        acciones.append(f'<a href="{url_detail}">✏️ Editar</a>')
        
        # Validar pago si aplica
        if obj.estado in ['CRE', 'RSP'] and not obj.esta_expirada:
            acciones.append('💳 Validar Pago')
        
        # Ver boleto si existe
        try:
            boleto = obj.boleto
            url_boleto = reverse('admin:reservas_boleto_change', args=[boleto.pk])
            acciones.append(f'<a href="{url_boleto}">🎫 Ver Boleto</a>')
        except:
            pass
        
        return format_html(' | '.join(acciones))
    acciones.short_description = 'Acciones'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'pasajero', 'vuelo__origen_principal', 'vuelo__destino_principal'
        ).prefetch_related('detalles__asiento_vuelo__asiento')


@admin.register(AsientoVuelo)
class AsientoVueloAdmin(admin.ModelAdmin):
    """Admin para configuración de asientos por vuelo"""
    list_display = [
        'vuelo_codigo', 'asiento_info', 'tipo_asiento', 'precio',
        'habilitado_para_reserva', 'esta_reservado', 'configurado_por'
    ]
    list_filter = [
        'tipo_asiento', 'habilitado_para_reserva', 'vuelo__codigo_vuelo',
        'fecha_configuracion', 'activo'
    ]
    search_fields = [
        'vuelo__codigo_vuelo', 'asiento__numero', 'asiento__avion__modelo'
    ]
    readonly_fields = ['fecha_configuracion', 'esta_reservado']
    
    fieldsets = (
        ('Configuración Principal', {
            'fields': ('vuelo', 'escala_vuelo', 'asiento')
        }),
        ('Configuración de Precio y Tipo', {
            'fields': ('tipo_asiento', 'precio', 'habilitado_para_reserva')
        }),
        ('Control', {
            'fields': ('activo', 'esta_reservado')
        }),
        ('Auditoría', {
            'fields': ('fecha_configuracion', 'configurado_por'),
            'classes': ('collapse',)
        }),
    )
    
    def vuelo_codigo(self, obj):
        return obj.vuelo.codigo_vuelo
    vuelo_codigo.short_description = 'Vuelo'
    
    def asiento_info(self, obj):
        asiento = obj.asiento
        escala_info = f" (Escala {obj.escala_vuelo.orden})" if obj.escala_vuelo else ""
        return f"{asiento.numero} - {asiento.avion.modelo}{escala_info}"
    asiento_info.short_description = 'Asiento'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'vuelo', 'asiento__avion', 'escala_vuelo', 'configurado_por'
        )


@admin.register(Boleto)
class BoletoAdmin(admin.ModelAdmin):
    """Admin para boletos generados"""
    list_display = [
        'codigo_barras', 'reserva_info', 'pasajero_info', 'vuelo_info',
        'fecha_emision', 'usado', 'fecha_uso'
    ]
    list_filter = ['usado', 'fecha_emision', 'activo']
    search_fields = [
        'codigo_barras', 'reserva__codigo_reserva', 
        'reserva__pasajero__username', 'reserva__vuelo__codigo_vuelo'
    ]
    readonly_fields = [
        'codigo_barras', 'fecha_emision', 'vuelo_snapshot', 
        'asientos_snapshot', 'pasajero_snapshot'
    ]
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('codigo_barras', 'reserva', 'fecha_emision')
        }),
        ('Estado de Uso', {
            'fields': ('usado', 'fecha_uso', 'activo')
        }),
        ('Snapshots (Solo Lectura)', {
            'fields': ('vuelo_snapshot', 'asientos_snapshot', 'pasajero_snapshot'),
            'classes': ('collapse',)
        }),
    )
    
    def reserva_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>Estado: {}</small>',
            obj.reserva.codigo_reserva,
            obj.reserva.get_estado_display()
        )
    reserva_info.short_description = 'Reserva'
    
    def pasajero_info(self, obj):
        pasajero = obj.reserva.pasajero
        nombre = pasajero.get_full_name() or pasajero.username
        return format_html('<strong>{}</strong><br><small>{}</small>', nombre, pasajero.email)
    pasajero_info.short_description = 'Pasajero'
    
    def vuelo_info(self, obj):
        vuelo = obj.reserva.vuelo
        origen = vuelo.origen_principal.nombre if vuelo.origen_principal else 'N/A'
        destino = vuelo.destino_principal.nombre if vuelo.destino_principal else 'N/A'
        return format_html('{}<br><small>{} → {}</small>', vuelo.codigo_vuelo, origen, destino)
    vuelo_info.short_description = 'Vuelo'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'reserva__pasajero', 'reserva__vuelo__origen_principal', 'reserva__vuelo__destino_principal'
        )


@admin.register(ReservaDetalle)
class ReservaDetalleAdmin(admin.ModelAdmin):
    """Admin para detalles de reserva"""
    list_display = [
        'reserva_codigo', 'asiento_info', 'precio_pagado', 'fecha_asignacion'
    ]
    list_filter = [
        'asiento_vuelo__tipo_asiento', 'fecha_asignacion',
        'reserva__estado', 'asiento_vuelo__vuelo__codigo_vuelo'
    ]
    search_fields = [
        'reserva__codigo_reserva', 'asiento_vuelo__asiento__numero',
        'asiento_vuelo__vuelo__codigo_vuelo'
    ]
    readonly_fields = ['fecha_asignacion']
    
    def reserva_codigo(self, obj):
        return obj.reserva.codigo_reserva
    reserva_codigo.short_description = 'Reserva'
    
    def asiento_info(self, obj):
        asiento = obj.asiento_vuelo.asiento
        tipo = obj.asiento_vuelo.get_tipo_asiento_display()
        return f"{asiento.numero} ({tipo}) - {asiento.avion.modelo}"
    asiento_info.short_description = 'Asiento'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'reserva', 'asiento_vuelo__asiento__avion', 'asiento_vuelo__vuelo'
        )


# Configuraciones adicionales del admin
admin.site.site_header = "Gestión de Vuelos - Administración"
admin.site.site_title = "Admin Vuelos"
admin.site.index_title = "Panel de Administración de Reservas"