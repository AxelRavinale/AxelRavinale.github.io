from django import forms
from .models import Pasajero

class PasajeroForm(forms.ModelForm):
    class Meta:
        model = Pasajero
        fields = ['nombre', 'apellido', 'dni', 'email', 'telefono']
