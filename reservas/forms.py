from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Reserva, AsientoVuelo, Boleto
from vuelos.models import Vuelo


class ReservaForm(forms.ModelForm):
    """Formulario para crear reservas (usado principalmente por admin)"""
    
    class Meta:
        model = Reserva
        fields = ['pasajero', 'vuelo']
        widgets = {
            'pasajero': forms.Select(attrs={'class': 'form-control'}),
            'vuelo': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            if user.is_superuser:
                # Admin puede crear reservas para cualquier usuario
                self.fields['pasajero'].queryset = User.objects.filter(
                    is_active=True, is_superuser=False
                ).order_by('username')
                
                # Admin puede ver todos los vuelos configurados
                self.fields['vuelo'].queryset = Vuelo.objects.filter(
                    activo=True,
                    configuracion_reserva__configurado=True,
                    fecha_salida_estimada__gt=timezone.now()
                ).order_by('fecha_salida_estimada')
            else:
                # Usuario normal solo puede crear reservas para sí mismo
                self.fields['pasajero'].initial = user
                self.fields['pasajero'].widget = forms.HiddenInput()
                
                # Solo vuelos disponibles
                self.fields['vuelo'].queryset = Vuelo.objects.filter(
                    activo=True,
                    configuracion_reserva__configurado=True,
                    fecha_salida_estimada__gt=timezone.now()
                ).order_by('fecha_salida_estimada')

    def clean_vuelo(self):
        vuelo = self.cleaned_data['vuelo']
        
        # Verificar que el vuelo esté configurado
        try:
            if not vuelo.configuracion_reserva.configurado:
                raise ValidationError(_("Este vuelo no está disponible para reservas"))
        except:
            raise ValidationError(_("Este vuelo no está configurado"))
        
        # Verificar que no haya pasado la fecha límite
        if vuelo.fecha_salida_estimada <= timezone.now():
            raise ValidationError(_("Este vuelo ya no acepta reservas"))
        
        return vuelo


class ConfiguracionAsientoForm(forms.ModelForm):
    """Formulario para configurar asientos individuales"""
    
    class Meta:
        model = AsientoVuelo
        fields = ['tipo_asiento', 'precio', 'habilitado_para_reserva']
        widgets = {
            'tipo_asiento': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'min': '0',
                'step': '0.01'
            }),
            'habilitado_para_reserva': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_precio(self):
        precio = self.cleaned_data['precio']
        if precio <= 0:
            raise ValidationError(_("El precio debe ser mayor a 0"))
        return precio


class PagoForm(forms.Form):
    """Formulario para procesar pagos ficticios"""
    
    METODOS_PAGO = [
        ('tarjeta_credito', 'Tarjeta de Crédito'),
        ('tarjeta_debito', 'Tarjeta de Débito'),
        ('efectivo', 'Efectivo (en sucursal)'),
    ]
    
    metodo_pago = forms.ChoiceField(
        choices=METODOS_PAGO,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_("Método de Pago")
    )
    
    # Campos para tarjeta (ficticios)
    numero_tarjeta = forms.CharField(
        max_length=19,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234 5678 9012 3456',
            'pattern': '[0-9\s]{13,19}',
        }),
        label=_("Número de Tarjeta"),
        required=False
    )
    
    titular = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre como aparece en la tarjeta'
        }),
        label=_("Titular de la Tarjeta"),
        required=False
    )
    
    mes_expiracion = forms.ChoiceField(
        choices=[(i, f"{i:02d}") for i in range(1, 13)],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_("Mes de Expiración"),
        required=False
    )
    
    año_expiracion = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(datetime.now().year, datetime.now().year + 10)],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_("Año de Expiración"),
        required=False
    )
    
    cvv = forms.CharField(
        max_length=4,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123',
            'pattern': '[0-9]{3,4}',
        }),
        label=_("CVV"),
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.reserva = kwargs.pop('reserva', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        metodo_pago = cleaned_data.get('metodo_pago')
        
        # Si es pago con tarjeta, validar campos de tarjeta
        if metodo_pago in ['tarjeta_credito', 'tarjeta_debito']:
            campos_requeridos = ['numero_tarjeta', 'titular', 'mes_expiracion', 'año_expiracion', 'cvv']
            
            for campo in campos_requeridos:
                if not cleaned_data.get(campo):
                    raise ValidationError(f"El campo {campo} es requerido para pagos con tarjeta")
            
            # Validar número de tarjeta (ficticio)
            numero_tarjeta = cleaned_data.get('numero_tarjeta', '').replace(' ', '')
            if len(numero_tarjeta) < 13 or len(numero_tarjeta) > 19:
                raise ValidationError(_("Número de tarjeta inválido"))
            
            # Validar CVV
            cvv = cleaned_data.get('cvv', '')
            if len(cvv) < 3 or len(cvv) > 4:
                raise ValidationError(_("CVV inválido"))
        
        return cleaned_data


class FiltroReservaForm(forms.Form):
    """Formulario para filtrar reservas"""
    
    codigo_reserva = forms.CharField(
        max_length=16,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Código de reserva'
        }),
        label=_("Código de Reserva")
    )
    
    vuelo = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Código de vuelo'
        }),
        label=_("Vuelo")
    )
    
    estado = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + Reserva.EstadoChoices.choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_("Estado")
    )
    
    pasajero = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre o email del pasajero'
        }),
        label=_("Pasajero")
    )


class BusquedaBoletoForm(forms.Form):
    """Formulario para buscar boletos por código de barras"""
    
    codigo_barras = forms.CharField(
        max_length=16,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el código de barras del boleto',
            'autofocus': True
        }),
        label=_("Código de Barras")
    )

    def clean_codigo_barras(self):
        codigo = self.cleaned_data['codigo_barras'].upper().strip()
        if len(codigo) < 8:
            raise ValidationError(_("El código debe tener al menos 8 caracteres"))
        return codigo


class BusquedaVuelosForm(forms.Form):
    """Formulario para buscar vuelos disponibles"""
    
    origen = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ciudad de origen'
        }),
        label=_("Origen")
    )
    
    destino = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ciudad de destino'
        }),
        label=_("Destino")
    )
    
    fecha = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_("Fecha de Salida")
    )

    def clean_fecha(self):
        fecha = self.cleaned_data.get('fecha')
        if fecha and fecha <= timezone.now().date():
            raise ValidationError(_("La fecha debe ser futura"))
        return fecha