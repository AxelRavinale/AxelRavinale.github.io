from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.forms import inlineformset_factory
from .models import Reserva, ReservaDetalle
from vuelos.models import Vuelo
from aviones.models import Asiento


class ReservaListView(LoginRequiredMixin, ListView):
    model = Reserva
    template_name = 'reserva_list.html'

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_superuser:
            qs = qs.filter(pasajero=self.request.user)
        vuelo = self.request.GET.get('vuelo')
        if vuelo:
            qs = qs.filter(vuelo__codigo_vuelo__icontains=vuelo)
        return qs


class ReservaDetailView(LoginRequiredMixin, DetailView):
    model = Reserva
    template_name = 'reserva_detail.html'

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_superuser:
            qs = qs.filter(pasajero=self.request.user)
        return qs

from django.views.generic import DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ReservaDetalle

class ReservaDetalleDeleteView(LoginRequiredMixin, DeleteView):
    model = ReservaDetalle
    template_name = 'reserva_detalle_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('reserva_detail', kwargs={'pk': self.object.reserva.pk})

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_superuser:
            qs = qs.filter(reserva__pasajero=self.request.user)
        return qs



class ReservaCreateView(LoginRequiredMixin, CreateView):
    model = Reserva
    fields = ['vuelo']
    template_name = 'reserva_form.html'
    success_url = reverse_lazy('reserva_list')

    def form_valid(self, form):
        form.instance.pasajero = self.request.user
        response = super().form_valid(form)
        return redirect('reserva_detalle_create', reserva_pk=self.object.pk)


class ReservaUpdateView(LoginRequiredMixin, UpdateView):
    model = Reserva
    fields = ['vuelo', 'estado', 'activo']
    template_name = 'reserva_form.html'
    success_url = reverse_lazy('reserva_list')

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_superuser:
            qs = qs.filter(pasajero=self.request.user)
        return qs


class ReservaDeleteView(LoginRequiredMixin, DeleteView):
    model = Reserva
    template_name = 'reserva_confirm_delete.html'
    success_url = reverse_lazy('reserva_list')

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_superuser:
            qs = qs.filter(pasajero=self.request.user)
        return qs


ReservaDetalleFormSet = inlineformset_factory(
    Reserva,
    ReservaDetalle,
    fields=['asiento', 'precio'],
    extra=1,
    can_delete=True
)


class ReservaDetalleCreateView(LoginRequiredMixin, FormView):
    template_name = 'reserva_detalle_form.html'
    form_class = ReservaDetalleFormSet
    success_url = reverse_lazy('reserva_list')

    def dispatch(self, request, *args, **kwargs):
        self.reserva = get_object_or_404(Reserva, pk=kwargs['reserva_pk'])
        if not request.user.is_superuser and self.reserva.pasajero != request.user:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        return ReservaDetalleFormSet(instance=self.reserva, **self.get_form_kwargs())

    def form_valid(self, form):
        form.instance = self.reserva
        detalles = form.save(commit=False)

        avion_asignado = self.reserva.vuelo.avion_asignado
        for detalle in detalles:
            if detalle.asiento.avion != avion_asignado:
                form.add_error('asiento', f"El asiento {detalle.asiento} no pertenece al avión asignado al vuelo.")
                return self.form_invalid(form)
            detalle.reserva = self.reserva
            detalle.save()

        for obj in form.deleted_objects:
            obj.delete()

        self.reserva.actualizar_precio_total()

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('reserva_detail', kwargs={'pk': self.reserva.pk})
