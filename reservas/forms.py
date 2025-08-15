from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db import models
from datetime import datetime
import re
from .models import AsientoVuelo, Vuelo, Reserva, ReservaDetalle


class SeleccionAsientosForm(forms.Form):
    """Formulario mejorado para seleccionar asientos"""
    
    def __init__(self, vuelo, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vuelo = vuelo
        self.asientos_data = self._get_asientos_data()
        
        # Crear campos dinámicamente
        self._create_filter_field()
        self._create_seats_field()
    
    def _create_filter_field(self):
        """Crear campo de filtros por tipo"""
        tipos_disponibles = set()
        for asiento_data in self.asientos_data:
            tipos_disponibles.add(asiento_data['tipo_asiento'])
        
        if tipos_disponibles:
            choices = []
            tipo_dict = dict(AsientoVuelo.TipoAsientoChoices.choices)
            for tipo in sorted(tipos_disponibles):
                choices.append((tipo, tipo_dict.get(tipo, tipo)))
            
            self.fields['filtro_tipo'] = forms.MultipleChoiceField(
                choices=choices,
                required=False,
                widget=forms.CheckboxSelectMultiple(attrs={
                    'class': 'form-check-input'
                })
            )
    
    def _create_seats_field(self):
        """Crear campo de asientos disponibles"""
        choices = []
        filtro_activo = self.data.getlist('filtro_tipo', []) if self.data else []
        
        for asiento_data in self.asientos_data:
            # Aplicar filtro si existe
            if filtro_activo and asiento_data['tipo_asiento'] not in filtro_activo:
                continue
                
            label = self._format_seat_label(asiento_data)
            choices.append((asiento_data['id'], label))
        
        self.fields['asientos_seleccionados'] = forms.MultipleChoiceField(
            choices=choices,
            required=False,
            widget=forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input asiento-checkbox'
            })
        )
    
    def _get_asientos_data(self):
        """Obtener datos de asientos disponibles - lógica mejorada"""
        asientos_data = []
        
        # Obtener asientos ocupados una sola vez
        asientos_ocupados = set(
            ReservaDetalle.objects.filter(
                asiento_vuelo__vuelo=self.vuelo,
                reserva__activo=True,
                reserva__estado__in=['CRE', 'CON', 'RSP']
            ).values_list('asiento_vuelo_id', flat=True)
        )
        
        if self.vuelo.tiene_escalas:
            # Vuelos con escalas
            for escala_vuelo in self.vuelo.escalas_vuelo.filter(activo=True).order_by('orden'):
                asientos_vuelo = AsientoVuelo.objects.filter(
                    vuelo=self.vuelo,
                    escala_vuelo=escala_vuelo,
                    activo=True,
                    habilitado_para_reserva=True
                ).select_related('asiento').exclude(id__in=asientos_ocupados)
                
                for av in asientos_vuelo:
                    asientos_data.append({
                        'id': av.id,
                        'numero': av.asiento.numero,
                        'fila': av.asiento.fila,
                        'columna': av.asiento.columna,
                        'tipo_asiento': av.tipo_asiento,
                        'tipo_display': av.get_tipo_asiento_display(),
                        'precio': float(av.precio),  # Convertir a float para JS
                        'escala_vuelo': escala_vuelo,
                        'escala_info': f"Escala {escala_vuelo.orden}: {escala_vuelo.origen} → {escala_vuelo.destino}"
                    })
        else:
            # Vuelos directos
            asientos_vuelo = AsientoVuelo.objects.filter(
                vuelo=self.vuelo,
                escala_vuelo__isnull=True,
                activo=True,
                habilitado_para_reserva=True
            ).select_related('asiento').exclude(id__in=asientos_ocupados)
            
            for av in asientos_vuelo:
                asientos_data.append({
                    'id': av.id,
                    'numero': av.asiento.numero,
                    'fila': av.asiento.fila,
                    'columna': av.asiento.columna,
                    'tipo_asiento': av.tipo_asiento,
                    'tipo_display': av.get_tipo_asiento_display(),
                    'precio': float(av.precio),  # Convertir a float para JS
                    'escala_vuelo': None,
                    'escala_info': None
                })
        
        # Ordenar por fila y columna
        return sorted(asientos_data, key=lambda x: (x['fila'], x['columna']))
    
    def _format_seat_label(self, asiento_data):
        """Formatear etiqueta del asiento de forma más clara"""
        label = f"{asiento_data['numero']} - {asiento_data['tipo_display']} - ${asiento_data['precio']:.2f}"
        if asiento_data['escala_info']:
            label = f"{asiento_data['escala_info']} | {label}"
        return label
    
    def clean_asientos_seleccionados(self):
        """Validar asientos seleccionados"""
        selected_ids = self.cleaned_data.get('asientos_seleccionados', [])
        
        if not selected_ids:
            raise ValidationError(_("Debe seleccionar al menos un asiento"))
        
        # Convertir a enteros
        try:
            selected_ids = [int(id_) for id_ in selected_ids]
        except ValueError:
            raise ValidationError(_("IDs de asientos inválidos"))
        
        # Verificar que existan y estén disponibles
        valid_ids = [data['id'] for data in self.asientos_data]
        invalid_ids = [id_ for id_ in selected_ids if id_ not in valid_ids]
        
        if invalid_ids:
            raise ValidationError(_("Algunos asientos ya no están disponibles"))
        
        # Verificar disponibilidad en tiempo real
        asientos_ocupados_ahora = set(
            ReservaDetalle.objects.filter(
                asiento_vuelo_id__in=selected_ids,
                reserva__activo=True,
                reserva__estado__in=['CRE', 'CON', 'RSP']
            ).values_list('asiento_vuelo_id', flat=True)
        )
        
        if asientos_ocupados_ahora:
            raise ValidationError(_("Algunos asientos fueron reservados por otro usuario. Actualice la página."))
        
        return selected_ids
    
    def get_precio_total(self):
        """Calcular precio total"""
        if not self.is_valid():
            return 0
        
        selected_ids = self.cleaned_data.get('asientos_seleccionados', [])
        if not selected_ids:
            return 0
        
        # Buscar precios en los datos cargados
        total = 0
        selected_ids = [int(id_) for id_ in selected_ids]
        
        for asiento_data in self.asientos_data:
            if asiento_data['id'] in selected_ids:
                total += asiento_data['precio']
        
        return total
    
    def get_asientos_info(self):
        """Obtener información detallada de asientos seleccionados"""
        if not self.is_valid():
            return []
        
        selected_ids = self.cleaned_data.get('asientos_seleccionados', [])
        if not selected_ids:
            return []
        
        selected_ids = [int(id_) for id_ in selected_ids]
        info = []
        
        for asiento_data in self.asientos_data:
            if asiento_data['id'] in selected_ids:
                info.append({
                    'id': asiento_data['id'],
                    'numero': asiento_data['numero'],
                    'tipo': asiento_data['tipo_display'],
                    'precio': asiento_data['precio'],
                    'escala': asiento_data['escala_vuelo'].orden if asiento_data['escala_vuelo'] else None,
                    'escala_info': asiento_data['escala_info']
                })
        
        return info



class PagoForm(forms.Form):
    """Formulario para procesar pagos"""
    
    METODOS_PAGO = [
        ('tarjeta_credito', 'Tarjeta de Crédito'),
        ('tarjeta_debito', 'Tarjeta de Débito'),
        ('efectivo', 'Efectivo'),
    ]
    
    metodo_pago = forms.ChoiceField(
        choices=METODOS_PAGO,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Método de Pago')
    )
    
    # Datos de tarjeta
    numero_tarjeta = forms.CharField(
        max_length=19,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234 5678 9012 3456',
            'maxlength': '19'
        }),
        label=_('Número de Tarjeta'),
        required=False
    )
    
    titular = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre como aparece en la tarjeta'
        }),
        label=_('Titular de la Tarjeta'),
        required=False
    )
    
    # Mes y año de expiración
    MESES = [(i, f"{i:02d}") for i in range(1, 13)]
    AÑOS = [(i, str(i)) for i in range(datetime.now().year, datetime.now().year + 15)]
    
    mes_expiracion = forms.ChoiceField(
        choices=MESES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Mes'),
        required=False
    )
    
    año_expiracion = forms.ChoiceField(
        choices=AÑOS,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Año'),
        required=False
    )
    
    cvv = forms.CharField(
        max_length=4,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123',
            'maxlength': '4'
        }),
        label=_('CVV'),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        self.reserva = kwargs.pop('reserva', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        metodo_pago = cleaned_data.get('metodo_pago')
        
        # Validar datos de tarjeta si no es efectivo
        if metodo_pago != 'efectivo':
            numero_tarjeta = cleaned_data.get('numero_tarjeta (pruebe 4111111111111111)')
            titular = cleaned_data.get('titular')        
            mes_expiracion = cleaned_data.get('mes_expiracion')
            año_expiracion = cleaned_data.get('año_expiracion')
            cvv = cleaned_data.get('cvv')
            
            if not numero_tarjeta:
                raise ValidationError(_('Número de tarjeta es requerido'))
            
            if not titular:
                raise ValidationError(_('Titular de la tarjeta es requerido'))
            
            if not mes_expiracion:
                raise ValidationError(_('Mes de expiración es requerido'))
            
            if not año_expiracion:
                raise ValidationError(_('Año de expiración es requerido'))
                
            if not cvv:
                raise ValidationError(_('CVV es requerido'))
            
            # Validar formato de número de tarjeta (solo dígitos)
            numero_limpio = numero_tarjeta.replace(' ', '').replace('-', '')
            if not numero_limpio.isdigit() or len(numero_limpio) < 13:
                raise ValidationError(_('Número de tarjeta inválido'))
            
            # Validar CVV
            if not cvv.isdigit() or len(cvv) < 3:
                raise ValidationError(_('CVV inválido'))
            
            # Validar fecha de expiración
            try:
                año = int(año_expiracion)
                mes = int(mes_expiracion)
                fecha_exp = datetime(año, mes, 1)
                if fecha_exp < datetime.now():
                    raise ValidationError(_('La tarjeta está expirada'))
            except (ValueError, TypeError):
                raise ValidationError(_('Fecha de expiración inválida'))
        
        return cleaned_data
    
    def clean_numero_tarjeta(self):
        numero = self.cleaned_data.get('numero_tarjeta', '')
        # Formatear número con espacios
        numero_limpio = numero.replace(' ', '').replace('-', '')
        if numero_limpio:
            # Agregar espacios cada 4 dígitos
            numero_formateado = ' '.join([numero_limpio[i:i+4] for i in range(0, len(numero_limpio), 4)])
            return numero_formateado
        return numero


class BusquedaBoletoForm(forms.Form):
    """Formulario para buscar boletos por código de barras"""
    
    codigo_barras = forms.CharField(
        max_length=16,
        min_length=8,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ingrese el código del boleto',
            'style': 'text-transform: uppercase;'
        }),
        label=_("Código de Boleto")
    )
    
    def clean_codigo_barras(self):
        codigo = self.cleaned_data['codigo_barras'].strip().upper()
        
        # Validar formato alfanumérico
        if not re.match(r'^[A-Z0-9]+,', codigo):
            raise ValidationError(_("El código debe contener solo letras y números"))
        
        return codigo


class FiltroReservaForm(forms.Form):
    """Formulario para filtrar reservas en el admin"""
    
    codigo_reserva = forms.CharField(
        required=False,
        max_length=16,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Código de reserva'
        }),
        label=_("Código de Reserva")
    )
    
    vuelo = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Código de vuelo'
        }),
        label=_("Vuelo")
    )
    
    estado = forms.ChoiceField(
        required=False,
        choices=[('', _('Todos los estados'))] + [
            ('CRE', _('Creada')),
            ('RSP', _('Reservado Sin Pago')),
            ('CON', _('Confirmada y Pagada')),
            ('CAN', _('Cancelada')),
            ('EXP', _('Expirada')),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_("Estado")
    )
    
    pasajero = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre o email del pasajero'
        }),
        label=_("Pasajero")
    )
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_("Fecha Desde")
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_("Fecha Hasta")
    )


class ReservaForm(forms.ModelForm):
    """Formulario básico para reservas (si es necesario)"""
    class Meta:
        model = Reserva
        fields = ['vuelo']  # Ajustar según necesidades


class ConfiguracionAsientoForm(forms.Form):
    """Formulario para configuración masiva de asientos"""
    tipo_asiento = forms.ChoiceField(
        choices=AsientoVuelo.TipoAsientoChoices.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_("Tipo de Asiento")
    )
    
    precio = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01'
        }),
        label=_("Precio")
    )
    
    habilitado_para_reserva = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_("Habilitado para Reserva")
    )