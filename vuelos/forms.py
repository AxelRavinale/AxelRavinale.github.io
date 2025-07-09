# vuelos/forms.py
from django import forms
from vuelos.models import Vuelo

class VueloForm(forms.ModelForm):
    class Meta:
        model = Vuelo
        fields = ['escala', 'avion', 'codigo_vuelo', 'activo']
        widgets = {
            'codigo_vuelo': forms.TextInput(attrs={'class': 'form-control'}),
            'escala': forms.Select(attrs={'class': 'form-select'}),
            'avion': forms.Select(attrs={'class': 'form-select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
