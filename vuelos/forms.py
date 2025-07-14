from django import forms
from django.forms import modelformset_factory, inlineformset_factory
from django.utils.timezone import localtime
from vuelos.models import Vuelo, EscalaVuelo, TripulacionVuelo, Escala
from core.models import Localidad, Persona
from aviones.models import Avion


class VueloForm(forms.ModelForm):
    escalas_existentes = forms.ModelMultipleChoiceField(
        queryset=Escala.objects.filter(activo=True),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select form-control'}),
        label='Seleccionar Escalas Existentes',
        help_text='Selecciona las escalas que deseas agregar a este vuelo.'
    )

    class Meta:
        model = Vuelo
        fields = [
            'codigo_vuelo',
            'origen_principal',
            'destino_principal',
            'avion_asignado',
            'fecha_salida_estimada',
            'fecha_llegada_estimada',
            'km_totales',
            'activo',

        ]
        widgets = {
            'fecha_salida_estimada': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_llegada_estimada': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'km_totales': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['origen_principal'].queryset = Localidad.objects.filter(activo=True)
        self.fields['destino_principal'].queryset = Localidad.objects.filter(activo=True)
        self.fields['avion_asignado'].queryset = Avion.objects.filter(activo=True)
        if self.instance and self.instance.pk:
            if self.instance.fecha_salida_estimada:
                fecha_salida = localtime(self.instance.fecha_salida_estimada).strftime('%Y-%m-%dT%H:%M')
                # Reemplazar el initial en el campo (no en attrs)
                self.initial['fecha_salida_estimada'] = fecha_salida

            if self.instance.fecha_llegada_estimada:
                fecha_llegada = localtime(self.instance.fecha_llegada_estimada).strftime('%Y-%m-%dT%H:%M')
                self.initial['fecha_llegada_estimada'] = fecha_llegada

# ========== Formulario de ESCALA específica por vuelo ==========


class EscalaForm(forms.ModelForm):
    class Meta:
        model = Escala
        fields = ['origen', 'destino', 'km_estimados', 'activo']
        widgets = {
            'km_estimados': forms.NumberInput(attrs={'class': 'form-control'}),
            'origen': forms.Select(attrs={'class': 'form-select'}),
            'destino': forms.Select(attrs={'class': 'form-select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

from django import forms

class EscalaVueloForm(forms.ModelForm):
    class Meta:
        model = EscalaVuelo
        fields = [
            'orden', 'escala', 'fecha_salida', 'fecha_llegada', 'avion', 'activo'
        ]
        widgets = {
            'fecha_salida': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_llegada': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'escala': forms.Select(attrs={'class': 'form-select'}),
            'avion': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['escala'].queryset = Escala.objects.filter(activo=True)
        self.fields['avion'].queryset = Avion.objects.filter(activo=True)

        # Formatear fechas para el widget datetime-local
        for field_name in ['fecha_salida', 'fecha_llegada']:
            if self.instance and getattr(self.instance, field_name):
                fecha = getattr(self.instance, field_name)
                # Formatear a "YYYY-MM-DDTHH:MM" (sin segundos)
                self.initial[field_name] = fecha.strftime('%Y-%m-%dT%H:%M')



EscalaVueloFormSet = inlineformset_factory(
    Vuelo,
    EscalaVuelo,
    form=EscalaVueloForm,
    extra=1,
    can_delete=True,
)




# ========== Formulario de TRIPULACIÓN ==========
class TripulacionVueloForm(forms.ModelForm):
    class Meta:
        model = TripulacionVuelo
        fields = ['persona', 'rol', 'activo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['persona'].queryset = Persona.objects.filter(activo=True)


TripulacionVueloFormSet = inlineformset_factory(
    Vuelo,                # Modelo padre
    TripulacionVuelo,     # Modelo hijo (relacionado con `vuelo = ForeignKey(...)`)
    form=TripulacionVueloForm,
    extra=1,
    can_delete=True
)


# ========== Filtros ==========
class VueloFiltroForm(forms.Form):
    fecha_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Fecha Desde'
    )
    fecha_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Fecha Hasta'
    )
    activo = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todos'),
            ('1', 'Activos'),
            ('0', 'Inactivos')
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Estado'
    )
    codigo_vuelo = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: AA123'}),
        label='Código de Vuelo'
    )
    avion = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Modelo o Matrícula'}),
        label='Avión'
    )

VueloFiltroFechaForm = VueloFiltroForm
