from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Persona
from .forms import PersonaForm

class PersonaCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Persona
    form_class = PersonaForm
    template_name = 'core/persona_form.html'
    success_url = reverse_lazy('home')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        from django.shortcuts import redirect
        from django.contrib import messages
        messages.error(self.request, "No tienes permisos para crear personas.")
        return redirect('home')
