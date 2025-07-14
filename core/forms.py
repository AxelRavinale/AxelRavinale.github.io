from django import forms
from django.core.exceptions import ValidationError
from .models import Persona, TipoDocumento, Genero, Localidad

class PersonaForm(forms.ModelForm):
    class Meta:
        model = Persona
        fields = [
            'nombre', 'apellido',
            'tipo_documento', 'numero_documento',
            'fecha_nacimiento', 'email',
            'localidad', 'genero', 'activo'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 'placeholder': 'ejemplo@dominio.com'
            }),
            'localidad': forms.Select(attrs={'class': 'form-select'}),
            'genero': forms.Select(attrs={'class': 'form-select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Solo activos, ordenados
        self.fields['tipo_documento'].queryset = TipoDocumento.objects.filter(activo=True).order_by('nombre')
        self.fields['genero'].queryset = Genero.objects.filter(activo=True).order_by('nombre')
        self.fields['localidad'].queryset = Localidad.objects.filter(activo=True).order_by('nombre')

    def clean_numero_documento(self):
        numero = self.cleaned_data['numero_documento']
        if Persona.objects.exclude(pk=self.instance.pk).filter(numero_documento=numero).exists():
            raise ValidationError("Este número de documento ya está en uso.")
        return numero

    def clean_email(self):
        email = self.cleaned_data['email']
        if Persona.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise ValidationError("Este email ya está registrado.")
        return email
