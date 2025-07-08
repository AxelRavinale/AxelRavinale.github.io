from django import forms
from django.contrib.auth.models import User
from .models import Trabajador

class UsuarioForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }

class TrabajadorForm(forms.ModelForm):
    class Meta:
        model = Trabajador
        fields = ['dni', 'cargo', 'telefono', 'fecha_ingreso']
