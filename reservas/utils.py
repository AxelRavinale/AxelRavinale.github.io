import io
import json
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.template.loader import get_template
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import qrcode
from PIL import Image
import logging

logger = logging.getLogger(__name__)


def generar_pdf_boleto(boleto):
    """
    Genera un PDF del boleto con código QR y toda la información del vuelo
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
    
    # Obtener estilos
    styles = getSampleStyleSheet()
    
    # Crear estilos personalizados
    titulo_style = ParagraphStyle(
        'TituloStyle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.darkblue,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    subtitulo_style = ParagraphStyle(
        'SubtituloStyle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.darkblue,
        alignment=TA_CENTER,
        spaceAfter=10
    )
    
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6
    )
    
    codigo_style = ParagraphStyle(
        'CodigoStyle',
        parent=styles['Normal'],
        fontSize=14,
        fontName='Courier-Bold',
        alignment=TA_CENTER,
        textColor=colors.red,
        borderWidth=1,
        borderColor=colors.black,
        borderPadding=8,
        spaceAfter=10
    )
    
    story = []
    
    # Título
    story.append(Paragraph("BOLETO ELECTRÓNICO", titulo_style))
    story.append(Paragraph(f"Código de Barras: {boleto.codigo_barras}", codigo_style))
    story.append(Spacer(1, 20))
    
    # Información del pasajero
    pasajero_data = boleto.pasajero_data
    story.append(Paragraph("INFORMACIÓN DEL PASAJERO", subtitulo_style))
    
    pasajero_info = [
        ['Nombre:', pasajero_data.get('full_name', 'N/A')],
        ['Email:', pasajero_data.get('email', 'N/A')],
        ['Reserva:', boleto.reserva.codigo_reserva],
    ]
    
    pasajero_table = Table(pasajero_info, colWidths=[4*cm, 10*cm])
    pasajero_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(pasajero_table)
    story.append(Spacer(1, 20))
    
    # Información del vuelo
    vuelo_data = boleto.vuelo_data
    story.append(Paragraph("INFORMACIÓN DEL VUELO", subtitulo_style))
    
    vuelo_info = [
        ['Código de Vuelo:', vuelo_data.get('codigo_vuelo', 'N/A')],
        ['Origen:', vuelo_data.get('origen', 'N/A')],
        ['Destino:', vuelo_data.get('destino', 'N/A')],
        ['Fecha de Salida:', _formatear_fecha(vuelo_data.get('fecha_salida'))],
        ['Fecha de Llegada:', _formatear_fecha(vuelo_data.get('fecha_llegada'))],
    ]
    
    vuelo_table = Table(vuelo_info, colWidths=[4*cm, 10*cm])
    vuelo_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(vuelo_table)
    story.append(Spacer(1, 20))
    
    # Escalas si existen
    if vuelo_data.get('tiene_escalas'):
        story.append(Paragraph("ESCALAS", subtitulo_style))
        escalas = vuelo_data.get('escalas', [])
        
        for i, escala in enumerate(escalas):
            escala_info = [
                [f'Escala {escala.get("orden", i+1)}:', ''],
                ['Origen:', escala.get('origen', 'N/A')],
                ['Destino:', escala.get('destino', 'N/A')],
                ['Salida:', _formatear_fecha(escala.get('fecha_salida'))],
                ['Llegada:', _formatear_fecha(escala.get('fecha_llegada'))],
                ['Avión:', escala.get('avion', 'N/A')],
            ]
            
            escala_table = Table(escala_info, colWidths=[4*cm, 10*cm])
            escala_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
            ]))
            
            story.append(escala_table)
            story.append(Spacer(1, 10))
    
    # Información de asientos
    story.append(Paragraph("ASIENTOS RESERVADOS", subtitulo_style))
    
    asientos_data = boleto.asientos_data
    asientos_headers = ['Asiento', 'Tipo', 'Precio', 'Avión']
    asientos_info = [asientos_headers]
    
    total_precio = 0
    for asiento in asientos_data:
        precio = float(asiento.get('precio', 0))
        total_precio += precio
        
        fila = [
            asiento.get('numero', 'N/A'),
            asiento.get('tipo', 'N/A'),
            f"${precio:.2f}",
            asiento.get('avion', 'N/A')
        ]
        
        if asiento.get('escala'):
            escala = asiento['escala']
            fila.append(f"Escala {escala.get('orden', '')}: {escala.get('origen', '')} - {escala.get('destino', '')}")
        
        asientos_info.append(fila)
    
    # Agregar fila de total
    asientos_info.append(['', '', f"TOTAL: ${total_precio:.2f}", ''])
    
    asientos_table = Table(asientos_info, colWidths=[3*cm, 4*cm, 3*cm, 4*cm])
    asientos_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightyellow),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(asientos_table)
    story.append(Spacer(1, 30))
    
    # Información importante
    story.append(Paragraph("INFORMACIÓN IMPORTANTE", subtitulo_style))
    
    info_importante = [
        "• Preséntese en el aeropuerto 2 horas antes del vuelo nacional, 3 horas para internacional.",
        "• Lleve un documento de identidad válido.",
        "• Verifique las restricciones de equipaje en nuestra página web.",
        "• Este boleto es válido solo para las fechas y vuelos especificados.",
        f"• Boleto emitido el {boleto.fecha_emision.strftime('%d/%m/%Y %H:%M')}",
    ]
    
    for info in info_importante:
        story.append(Paragraph(info, normal_style))
    
    story.append(Spacer(1, 20))
    
    # Generar código QR
    try:
        qr_data = {
            'boleto': boleto.codigo_barras,
            'reserva': boleto.reserva.codigo_reserva,
            'pasajero': pasajero_data.get('full_name', ''),
            'vuelo': vuelo_data.get('codigo_vuelo', ''),
        }
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)
        
        # Nota sobre QR (no se puede insertar imagen fácilmente en este contexto)
        story.append(Paragraph("CÓDIGO QR", subtitulo_style))
        story.append(Paragraph(f"Código QR generado para: {boleto.codigo_barras}", normal_style))
        
    except Exception as e:
        logger.error(f"Error generando QR: {e}")
    
    # Generar PDF
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf


def generar_pdf_detalle_reserva(reserva):
    """
    Genera un PDF con el detalle de la reserva (para reservas no pagadas)
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
    
    # Obtener estilos
    styles = getSampleStyleSheet()
    
    titulo_style = ParagraphStyle(
        'TituloStyle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.darkblue,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    subtitulo_style = ParagraphStyle(
        'SubtituloStyle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.darkblue,
        spaceAfter=10
    )
    
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6
    )
    
    codigo_style = ParagraphStyle(
        'CodigoStyle',
        parent=styles['Normal'],
        fontSize=16,
        fontName='Courier-Bold',
        alignment=TA_CENTER,
        textColor=colors.red,
        borderWidth=1,
        borderColor=colors.black,
        borderPadding=8,
        spaceAfter=10
    )
    
    story = []
    
    # Título
    story.append(Paragraph("DETALLE DE RESERVA", titulo_style))
    story.append(Paragraph(f"Código: {reserva.codigo_reserva}", codigo_style))
    story.append(Spacer(1, 20))
    
    # Estado de la reserva
    estado_color = colors.red if reserva.estado == 'RSP' else colors.green if reserva.estado == 'CON' else colors.orange
    estado_style = ParagraphStyle(
        'EstadoStyle',
        parent=styles['Normal'],
        fontSize=14,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        textColor=estado_color,
        spaceAfter=15
    )
    
    estado_texto = f"Estado: {reserva.get_estado_display()}"
    if reserva.estado == 'RSP' and reserva.fecha_limite_pago:
        estado_texto += f" - Límite de pago: {reserva.fecha_limite_pago.strftime('%d/%m/%Y %H:%M')}"
    
    story.append(Paragraph(estado_texto, estado_style))
    
    # Información del pasajero
    story.append(Paragraph("INFORMACIÓN DEL PASAJERO", subtitulo_style))
    
    pasajero_info = [
        ['Nombre:', reserva.pasajero.get_full_name() or reserva.pasajero.username],
        ['Email:', reserva.pasajero.email],
        ['Fecha de Reserva:', reserva.fecha_reserva.strftime('%d/%m/%Y %H:%M')],
    ]
    
    pasajero_table = Table(pasajero_info, colWidths=[4*cm, 10*cm])
    pasajero_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(pasajero_table)
    story.append(Spacer(1, 20))
    
    # Información del vuelo
    story.append(Paragraph("INFORMACIÓN DEL VUELO", subtitulo_style))
    
    vuelo_info = [
        ['Código de Vuelo:', reserva.vuelo.codigo_vuelo],
        ['Origen:', reserva.vuelo.origen_principal.nombre if reserva.vuelo.origen_principal else 'N/A'],
        ['Destino:', reserva.vuelo.destino_principal.nombre if reserva.vuelo.destino_principal else 'N/A'],
        ['Fecha de Salida:', reserva.vuelo.fecha_salida_estimada.strftime('%d/%m/%Y %H:%M') if reserva.vuelo.fecha_salida_estimada else 'N/A'],
        ['Fecha de Llegada:', reserva.vuelo.fecha_llegada_estimada.strftime('%d/%m/%Y %H:%M') if reserva.vuelo.fecha_llegada_estimada else 'N/A'],
    ]
    
    vuelo_table = Table(vuelo_info, colWidths=[4*cm, 10*cm])
    vuelo_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(vuelo_table)
    story.append(Spacer(1, 20))
    
    # Asientos reservados
    story.append(Paragraph("ASIENTOS RESERVADOS", subtitulo_style))
    
    asientos_headers = ['Asiento', 'Tipo', 'Precio']
    asientos_info = [asientos_headers]
    
    for detalle in reserva.detalles.all():
        asientos_info.append([
            detalle.asiento.numero,
            detalle.asiento_vuelo.get_tipo_asiento_display(),
            f"${detalle.precio_pagado:.2f}"
        ])
    
    # Total
    asientos_info.append(['', 'TOTAL:', f"${reserva.precio_total:.2f}"])
    
    asientos_table = Table(asientos_info, colWidths=[4*cm, 4*cm, 4*cm])
    asientos_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightyellow),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(asientos_table)
    story.append(Spacer(1, 30))
    
    # Instrucciones para el pago
    if reserva.estado == 'RSP':
        story.append(Paragraph("INSTRUCCIONES PARA EL PAGO", subtitulo_style))
        
        instrucciones = [
            f"• Esta reserva debe ser pagada antes del {reserva.fecha_limite_pago.strftime('%d/%m/%Y %H:%M')}",
            "• Ingrese a su cuenta en nuestra página web para realizar el pago",
            "• También puede realizar el pago en nuestras sucursales",
            "• Una vez realizado el pago, recibirá su boleto electrónico",
            "• Si no realiza el pago a tiempo, la reserva será cancelada automáticamente",
        ]
        
        for instruccion in instrucciones:
            story.append(Paragraph(instruccion, normal_style))
    
    story.append(Spacer(1, 20))
    
    # Información adicional
    story.append(Paragraph("INFORMACIÓN IMPORTANTE", subtitulo_style))
    
    info_adicional = [
        "• Esta reserva NO es un boleto válido para viajar",
        "• Para viajar necesita el boleto electrónico que se genera después del pago",
        "• Guarde este documento como comprobante de su reserva",
        f"• Documento generado el {reserva.fecha_creacion.strftime('%d/%m/%Y %H:%M')}",
    ]
    
    for info in info_adicional:
        story.append(Paragraph(info, normal_style))
    
    # Generar PDF
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf


def _formatear_fecha(fecha_iso):
    """
    Formatea una fecha ISO a formato legible
    """
    if not fecha_iso:
        return 'N/A'
    
    try:
        fecha = datetime.fromisoformat(fecha_iso.replace('Z', '+00:00'))
        return fecha.strftime('%d/%m/%Y %H:%M')
    except:
        return fecha_iso


def limpiar_reservas_expiradas():
    """
    Función para limpiar reservas expiradas (para ejecutar como tarea programada)
    """
    from .models import Reserva
    from django.utils import timezone
    
    # Buscar reservas expiradas
    reservas_expiradas = Reserva.objects.filter(
        activo=True,
        estado__in=[Reserva.EstadoChoices.CREADA, Reserva.EstadoChoices.RESERVADO_SIN_PAGO],
        fecha_limite_pago__lt=timezone.now()
    )
    
    count = 0
    for reserva in reservas_expiradas:
        try:
            reserva.estado = Reserva.EstadoChoices.EXPIRADA
            reserva.activo = False
            reserva.save()
            count += 1
            logger.info(f"Reserva {reserva.codigo_reserva} marcada como expirada")
        except Exception as e:
            logger.error(f"Error marcando reserva {reserva.codigo_reserva} como expirada: {e}")
    
    logger.info(f"Proceso de limpieza completado. {count} reservas marcadas como expiradas")
    return count


def generar_codigo_unico(modelo, campo, longitud=8):
    """
    Genera un código único para un modelo y campo específico
    """
    import secrets
    import string
    
    while True:
        codigo = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(longitud))
        if not modelo.objects.filter(**{campo: codigo}).exists():
            return codigo


def validar_disponibilidad_asientos(vuelo, asientos_ids):
    """
    Valida que los asientos estén disponibles para reserva
    """
    from .models import AsientoVuelo, ReservaDetalle, Reserva
    
    asientos_vuelo = AsientoVuelo.objects.filter(
        id__in=asientos_ids,
        vuelo=vuelo,
        activo=True,
        habilitado_para_reserva=True
    )
    
    if len(asientos_vuelo) != len(asientos_ids):
        return False, "Algunos asientos seleccionados no son válidos"
    
    # Verificar disponibilidad
    for asiento_vuelo in asientos_vuelo:
        if asiento_vuelo.esta_reservado:
            return False, f"El asiento {asiento_vuelo.asiento.numero} ya está reservado"
    
    return True, "Asientos disponibles"


def calcular_estadisticas_vuelo(vuelo):
    """
    Calcula estadísticas de ocupación y ventas de un vuelo
    """
    from .models import AsientoVuelo, ReservaDetalle, Reserva
    
    # Asientos configurados
    total_asientos = AsientoVuelo.objects.filter(
        vuelo=vuelo,
        activo=True,
        habilitado_para_reserva=True
    ).count()
    
    # Asientos reservados (pagados y sin pagar)
    asientos_reservados = ReservaDetalle.objects.filter(
        asiento_vuelo__vuelo=vuelo,
        reserva__activo=True,
        reserva__estado__in=[
            Reserva.EstadoChoices.CONFIRMADA,
            Reserva.EstadoChoices.RESERVADO_SIN_PAGO
        ]
    ).count()
    
    # Solo asientos pagados
    asientos_pagados = ReservaDetalle.objects.filter(
        asiento_vuelo__vuelo=vuelo,
        reserva__activo=True,
        reserva__estado=Reserva.EstadoChoices.CONFIRMADA
    ).count()
    
    # Ingresos generados
    ingresos = Reserva.objects.filter(
        vuelo=vuelo,
        activo=True,
        estado=Reserva.EstadoChoices.CONFIRMADA
    ).aggregate(total=models.Sum('precio_total'))['total'] or 0
    
    return {
        'total_asientos': total_asientos,
        'asientos_reservados': asientos_reservados,
        'asientos_disponibles': total_asientos - asientos_reservados,
        'asientos_pagados': asientos_pagados,
        'asientos_pendientes': asientos_reservados - asientos_pagados,
        'porcentaje_ocupacion': round((asientos_reservados / total_asientos * 100), 2) if total_asientos > 0 else 0,
        'porcentaje_pagados': round((asientos_pagados / total_asientos * 100), 2) if total_asientos > 0 else 0,
        'ingresos_generados': float(ingresos)
    }