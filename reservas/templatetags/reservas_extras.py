from django import template
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from decimal import Decimal

register = template.Library()


@register.filter
def currency(value):
    """Formatea un valor como moneda"""
    try:
        if value is None:
            return "$0.00"
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"


@register.filter
def asiento_estado_badge(estado):
    """Retorna un badge HTML según el estado del asiento"""
    badges = {
        'libre': '<span class="badge bg-success">Libre</span>',
        'reservado': '<span class="badge bg-warning">Reservado</span>',
        'ocupado': '<span class="badge bg-danger">Ocupado</span>',
    }
    return mark_safe(badges.get(estado.lower(), f'<span class="badge bg-secondary">{estado}</span>'))


@register.filter
def reserva_estado_badge(estado):
    """Retorna un badge HTML según el estado de la reserva"""
    badges = {
        'CRE': '<span class="badge bg-primary">Creada</span>',
        'RSP': '<span class="badge bg-warning">Sin Pago</span>',
        'CON': '<span class="badge bg-success">Confirmada</span>',
        'CAN': '<span class="badge bg-danger">Cancelada</span>',
        'EXP': '<span class="badge bg-dark">Expirada</span>',
    }
    return mark_safe(badges.get(estado, f'<span class="badge bg-secondary">{estado}</span>'))


@register.filter
def tipo_asiento_icon(tipo):
    """Retorna un icono según el tipo de asiento"""
    icons = {
        'ECO': '🪑',
        'PRE': '🛏️',
        'EJE': '💺',
        'PRI': '👑',
    }
    return icons.get(tipo, '🪑')


@register.filter
def horas_restantes_color(horas):
    """Retorna una clase CSS según las horas restantes"""
    if horas is None:
        return ''
    
    if horas <= 24:
        return 'text-danger fw-bold'
    elif horas <= 48:
        return 'text-warning fw-bold'
    else:
        return 'text-success'


@register.simple_tag
def progreso_configuracion(configurados, total):
    """Genera una barra de progreso para la configuración de asientos"""
    if total == 0:
        porcentaje = 0
    else:
        porcentaje = (configurados / total) * 100
    
    if porcentaje < 30:
        clase = 'bg-danger'
    elif porcentaje < 70:
        clase = 'bg-warning'
    else:
        clase = 'bg-success'
    
    return format_html(
        '<div class="progress" style="height: 20px;">'
        '<div class="progress-bar {}" role="progressbar" style="width: {}%;" '
        'aria-valuenow="{}" aria-valuemin="0" aria-valuemax="100">'
        '{}/{} ({}%)'
        '</div>'
        '</div>',
        clase, porcentaje, configurados, configurados, total, int(porcentaje)
    )


@register.inclusion_tag('reservas/templatetags/asiento_card.html')
def asiento_card(asiento_vuelo, ocupado=False, seleccionable=True):
    """Template tag para mostrar una tarjeta de asiento"""
    return {
        'asiento_vuelo': asiento_vuelo,
        'ocupado': ocupado,
        'seleccionable': seleccionable,
        'asiento': asiento_vuelo.asiento,
        'precio': asiento_vuelo.precio,
        'tipo': asiento_vuelo.get_tipo_asiento_display(),
        'tipo_codigo': asiento_vuelo.tipo_asiento,
    }


@register.inclusion_tag('reservas/templatetags/reserva_timeline.html')
def reserva_timeline(reserva):
    """Timeline del estado de una reserva"""
    estados = []
    
    # Siempre existe la fecha de creación
    estados.append({
        'titulo': 'Reserva Creada',
        'fecha': reserva.fecha_reserva,
        'icono': '📝',
        'completado': True,
        'activo': reserva.estado == 'CRE'
    })
    
    # Estado de pago
    if reserva.estado in ['RSP', 'CON']:
        estados.append({
            'titulo': 'En Espera de Pago',
            'fecha': reserva.fecha_reserva,
            'icono': '⏰',
            'completado': True,
            'activo': reserva.estado == 'RSP'
        })
    
    # Confirmación
    if reserva.estado == 'CON' and reserva.fecha_pago:
        estados.append({
            'titulo': 'Pago Confirmado',
            'fecha': reserva.fecha_pago,
            'icono': '✅',
            'completado': True,
            'activo': True
        })
    
    # Cancelación
    if reserva.estado == 'CAN':
        estados.append({
            'titulo': 'Reserva Cancelada',
            'fecha': reserva.fecha_modificacion,
            'icono': '❌',
            'completado': True,
            'activo': True,
            'error': True
        })
    
    return {'estados': estados, 'reserva': reserva}


@register.filter
def suma_precios(detalles):
    """Suma los precios de una lista de detalles de reserva"""
    total = Decimal('0.00')
    for detalle in detalles:
        if hasattr(detalle, 'precio_pagado'):
            total += detalle.precio_pagado
        elif hasattr(detalle, 'precio'):
            total += detalle.precio
    return total


@register.filter
def formato_duracion(timedelta_obj):
    """Formatea un timedelta a formato legible"""
    if not timedelta_obj:
        return "N/A"
    
    total_seconds = int(timedelta_obj.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


@register.simple_tag
def get_asiento_status(asiento_vuelo, asientos_ocupados):
    """Determina el status de un asiento"""
    if asiento_vuelo.asiento.id in asientos_ocupados:
        return 'ocupado'
    elif not asiento_vuelo.habilitado_para_reserva:
        return 'deshabilitado'
    else:
        return 'libre'


@register.filter
def mask_card_number(numero):
    """Enmascara un número de tarjeta mostrando solo los últimos 4 dígitos"""
    if not numero or len(numero) < 4:
        return "****-****-****-****"
    
    masked = "*" * (len(numero) - 4) + numero[-4:]
    # Formatear con guiones cada 4 dígitos
    formatted = ""
    for i, char in enumerate(masked):
        if i > 0 and i % 4 == 0:
            formatted += "-"
        formatted += char
    
    return formatted[:19]  # Máximo 19 caracteres


@register.simple_tag
def url_with_params(request, **kwargs):
    """Construye una URL manteniendo los parámetros actuales y agregando nuevos"""
    params = request.GET.copy()
    for key, value in kwargs.items():
        if value:
            params[key] = value
        elif key in params:
            del params[key]
    
    if params:
        return f"?{params.urlencode()}"
    return ""