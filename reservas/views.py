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


class ReservaListView(ListView):
    model = Reserva
    template_name = 'reserva_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()

        # Solo mostrar reservas del usuario logueado
        if self.request.user.is_authenticated and not self.request.user.is_superuser:
            queryset = queryset.filter(pasajero=self.request.user)

        # Filtros opcionales
        vuelo = self.request.GET.get('vuelo')
        if vuelo:
            queryset = queryset.filter(vuelo__codigo_vuelo__icontains=vuelo)

        return queryset


