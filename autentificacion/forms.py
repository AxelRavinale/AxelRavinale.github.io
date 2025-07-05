from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class RegisterForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        strip=True,
        label='Nombre de usuario',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={'required': 'Este campo es obligatorio', 'max_length': 'Máximo 150 caracteres'}
    )
    email = forms.EmailField(
        label='Correo Electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        error_messages={'required': 'Este campo es obligatorio', 'invalid': 'Correo inválido'}
    )
    password1 = forms.CharField(
        max_length=150,
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    password2 = forms.CharField(
        max_length=150,
        label='Repetir contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError("El usuario ya existe")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("El correo ya existe")
        return email

    def clean(self):
        cleaned_data = super().clean()
        pass1 = cleaned_data.get('password1')
        pass2 = cleaned_data.get('password2')

        if pass1 and pass2 and pass1 != pass2:
            self.add_error('password2', "Las contraseñas no coinciden")

    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
        )
        return user


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Nombre de usuario',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label='Contraseña',
        max_length=150,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )