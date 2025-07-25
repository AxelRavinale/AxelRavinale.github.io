from django import forms
from django.forms import modelformset_factory, inlineformset_factory
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _
from vuelos.models import Vuelo, EscalaVuelo, TripulacionVuelo, Escala
from core.models import Localidad, Persona
from aviones.models import Avion


class VueloForm(forms.ModelForm):
    escalas_existentes = forms.ModelMultipleChoiceField(
        queryset=Escala.objects.filter(activo=True),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select form-control'}),
        label=_('Seleccionar Escalas Existentes'),
        help_text=_('Selecciona las escalas que deseas agregar a este vuelo.')
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
            'codigo_vuelo': forms.TextInput(attrs={'class': 'form-control'}),
            'origen_principal': forms.Select(attrs={'class': 'form-select'}),
            'destino_principal': forms.Select(attrs={'class': 'form-select'}),
            'avion_asignado': forms.Select(attrs={'class': 'form-select'}),
            'fecha_salida_estimada': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'fecha_llegada_estimada': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'km_totales': forms.NumberInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'codigo_vuelo': _('Código de Vuelo'),
            'origen_principal': _('Origen Principal'),
            'destino_principal': _('Destino Principal'),
            'avion_asignado': _('Avión Asignado'),
            'fecha_salida_estimada': _('Fecha de Salida Estimada'),
            'fecha_llegada_estimada': _('Fecha de Llegada Estimada'),
            'km_totales': _('Kilómetros Totales'),
            'activo': _('Activo'),
        }
        help_texts = {
            'codigo_vuelo': _('Ingrese el código único del vuelo (ej: AA123)'),
            'fecha_salida_estimada': _('Seleccione la fecha y hora de salida'),
            'fecha_llegada_estimada': _('Seleccione la fecha y hora de llegada'),
            'km_totales': _('Distancia total en kilómetros'),
            'activo': _('Marque si el vuelo está activo'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['origen_principal'].queryset = Localidad.objects.filter(activo=True)
        self.fields['destino_principal'].queryset = Localidad.objects.filter(activo=True)
        self.fields['avion_asignado'].queryset = Avion.objects.filter(activo=True)
        
        # Etiquetas vacías para los selects
        self.fields['origen_principal'].empty_label = _("Seleccione origen")
        self.fields['destino_principal'].empty_label = _("Seleccione destino")
        self.fields['avion_asignado'].empty_label = _("Seleccione avión")
        
        if self.instance and self.instance.pk:
            if self.instance.fecha_salida_estimada:
                fecha_salida = localtime(self.instance.fecha_salida_estimada).strftime('%Y-%m-%dT%H:%M')
                self.initial['fecha_salida_estimada'] = fecha_salida

            if self.instance.fecha_llegada_estimada:
                fecha_llegada = localtime(self.instance.fecha_llegada_estimada).strftime('%Y-%m-%dT%H:%M')
                self.initial['fecha_llegada_estimada'] = fecha_llegada


class EscalaForm(forms.ModelForm):
    class Meta:
        model = Escala
        fields = ['origen', 'destino', 'km_estimados', 'activo']
        widgets = {
            'origen': forms.Select(attrs={'class': 'form-select'}),
            'destino': forms.Select(attrs={'class': 'form-select'}),
            'km_estimados': forms.NumberInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'origen': _('Origen'),
            'destino': _('Destino'),
            'km_estimados': _('Kilómetros Estimados'),
            'activo': _('Activo'),
        }
        help_texts = {
            'km_estimados': _('Distancia estimada en kilómetros'),
            'activo': _('Marque si la escala está activa'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['origen'].queryset = Localidad.objects.filter(activo=True)
        self.fields['destino'].queryset = Localidad.objects.filter(activo=True)
        self.fields['origen'].empty_label = _("Seleccione origen")
        self.fields['destino'].empty_label = _("Seleccione destino")


class EscalaVueloForm(forms.ModelForm):
    class Meta:
        model = EscalaVuelo
        fields = [
            'orden', 'escala', 'fecha_salida', 'fecha_llegada', 'avion', 'activo'
        ]
        widgets = {
            'orden': forms.NumberInput(attrs={'class': 'form-control'}),
            'escala': forms.Select(attrs={'class': 'form-select'}),
            'fecha_salida': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'fecha_llegada': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'avion': forms.Select(attrs={'class': 'form-select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'orden': _('Orden'),
            'escala': _('Escala'),
            'fecha_salida': _('Fecha de Salida'),
            'fecha_llegada': _('Fecha de Llegada'),
            'avion': _('Avión'),
            'activo': _('Activo'),
        }
        help_texts = {
            'orden': _('Orden de la escala en el vuelo'),
            'fecha_salida': _('Fecha y hora de salida de esta escala'),
            'fecha_llegada': _('Fecha y hora de llegada de esta escala'),
            'activo': _('Marque si la escala está activa'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['escala'].queryset = Escala.objects.filter(activo=True)
        self.fields['avion'].queryset = Avion.objects.filter(activo=True)
        
        # Etiquetas vacías
        self.fields['escala'].empty_label = _("Seleccione escala")
        self.fields['avion'].empty_label = _("Seleccione avión")

        # Formatear fechas para el widget datetime-local
        for field_name in ['fecha_salida', 'fecha_llegada']:
            if self.instance and getattr(self.instance, field_name):
                fecha = getattr(self.instance, field_name)
                self.initial[field_name] = fecha.strftime('%Y-%m-%dT%H:%M')


EscalaVueloFormSet = inlineformset_factory(
    Vuelo,
    EscalaVuelo,
    form=EscalaVueloForm,
    extra=1,
    can_delete=True,
)


class TripulacionVueloForm(forms.ModelForm):
    class Meta:
        model = TripulacionVuelo
        fields = ['persona', 'rol', 'activo']
        widgets = {
            'persona': forms.Select(attrs={'class': 'form-select'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'persona': _('Persona'),
            'rol': _('Rol'),
            'activo': _('Activo'),
        }
        help_texts = {
            'rol': _('Seleccione el rol de la persona en la tripulación'),
            'activo': _('Marque si la asignación está activa'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['persona'].queryset = Persona.objects.filter(activo=True)
        
        # Etiquetas vacías
        self.fields['persona'].empty_label = _("Seleccione persona")
        self.fields['rol'].empty_label = _("Seleccione rol")


TripulacionVueloFormSet = inlineformset_factory(
    Vuelo,
    TripulacionVuelo,
    form=TripulacionVueloForm,
    extra=1,
    can_delete=True
)


class VueloFiltroForm(forms.Form):
    fecha_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label=_('Fecha Desde')
    )
    fecha_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label=_('Fecha Hasta')
    )
    activo = forms.ChoiceField(
        required=False,
        choices=[
            ('', _('Todos')),
            ('1', _('Activos')),
            ('0', _('Inactivos'))
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Estado')
    )
    codigo_vuelo = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ej: AA123')}),
        label=_('Código de Vuelo')
    )
    avion = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Modelo o Matrícula')}),
        label=_('Avión')
    )


VueloFiltroFechaForm = VueloFiltroForm