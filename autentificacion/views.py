from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.mail import EmailMessage
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.utils.translation import activate, get_language, deactivate
from django.views import View

from .forms import RegisterForm, LoginForm


class RegisterView(View):
    def get(self, request):
        form = RegisterForm()
        return render(request, 'register.html', {'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, _("Registro exitoso. ¡Bienvenido/a!"))
            return redirect('login')
        return render(request, 'register.html', {'form': form})


class LoginView(View):
    def get(self, request):
        form = LoginForm()
        return render(request, 'login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, _("Inicio de sesión exitoso."))
                return redirect('home')
            else:
                messages.error(request, _("Usuario o contraseña incorrectos."))
        return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, _("Sesión cerrada correctamente."))
    return redirect('login')


def change_language(request, lang_code):
    if lang_code in dict(settings.LANGUAGES).keys():
        activate(lang_code)
        request.session[settings.LANGUAGE_COOKIE_NAME] = lang_code
    return redirect(request.META.get('HTTP_REFERER', '/'))