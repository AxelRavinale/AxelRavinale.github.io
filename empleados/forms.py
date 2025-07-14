from django import forms
from django.contrib.auth.models import User
from .models import Trabajador
from django.core.exceptions import ValidationError


class UsuarioForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        widgets = {
            'password': forms.PasswordInput(render_value=True)
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].required = False

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("Este email ya está en uso.")
        return email


class TrabajadorForm(forms.ModelForm):
    class Meta:
        model = Trabajador
        fields = ['cargo', 'telefono', 'dni', 'fecha_ingreso']
        widgets = {
            'fecha_ingreso': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super(TrabajadorForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.fecha_ingreso:
            self.fields['fecha_ingreso'].initial = self.instance.fecha_ingreso.strftime('%Y-%m-%d')