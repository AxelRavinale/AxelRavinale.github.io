from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Reserva

class ReservaListView(ListView):
    model = Reserva
    template_name = 'reserva_list.html'

class ReservaCreateView(CreateView):
    model = Reserva
    fields = '__all__'
    template_name = 'reserva_form.html'
    success_url = reverse_lazy('reserva_list')

class ReservaDetailView(DetailView):
    model = Reserva
    template_name = 'reserva_detail.html'

class ReservaUpdateView(UpdateView):
    model = Reserva
    fields = '__all__'
    template_name = 'reserva_form.html'
    success_url = reverse_lazy('reserva_list')

class ReservaDeleteView(DeleteView):
    model = Reserva
    template_name = 'reserva_confirm_delete.html'
    success_url = reverse_lazy('reserva_list')
