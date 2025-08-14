import re
from django import template

register = template.Library()

@register.filter(name='extract_price')
def extract_price(value):
    """Extrae el precio de una cadena como '$123.45'"""
    if not value:
        return '0'
    
    # Buscar patrón $123.45 o $123
    price_match = re.search(r'\$(\d+(?:\.\d{2})?)', str(value))
    if price_match:
        return price_match.group(1)
    
    # Si no encuentra precio, retornar 0
    return '0'

@register.filter(name='extract_seat_number')
def extract_seat_number(value):
    """Extrae el número de asiento antes del primer guión"""
    if not value:
        return ''
    
    # Dividir por el primer ' - ' y tomar la primera parte
    parts = str(value).split(' - ', 1)
    return parts[0].strip() if parts else str(value)

@register.filter(name='regex_replace')
def regex_replace(value, pattern_replacement):
    """
    Reemplazo usando regex. 
    Uso: {{ value|regex_replace:'patron|reemplazo' }}
    """
    if not value or not pattern_replacement:
        return value
    
    try:
        parts = pattern_replacement.split('|', 1)
        if len(parts) != 2:
            return value
        
        pattern, replacement = parts
        return re.sub(pattern, replacement, str(value))
    except Exception:
        return value