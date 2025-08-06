from django import forms
from .models import Avion

class AvionForm(forms.ModelForm):
    class Meta:
        model = Avion
        fields = [
            'fabricante', 'modelo', 'capacidad', 'matricula',
            'tipo', 'autonomia_km', 'fecha_fabricacion', 'en_mantenimiento'
        ]
        widgets = {
            'fecha_fabricacion': forms.DateInput(attrs={'type': 'date'}),
        }
