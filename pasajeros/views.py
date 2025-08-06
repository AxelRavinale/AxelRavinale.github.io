from django.shortcuts import render, redirect, get_object_or_404
from .models import Pasajero
from .forms import PasajeroForm
from django.contrib import messages

def lista_pasajeros(request):
    pasajeros = Pasajero.objects.filter(activo=True)
    return render(request, 'pasajeros/lista_pasajeros.html', {'pasajeros': pasajeros})

def registrar_pasajero(request):
    if request.method == 'POST':
        form = PasajeroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Pasajero registrado correctamente.")
            return redirect('lista_pasajeros')
    else:
        form = PasajeroForm()
    return render(request, 'pasajeros/registrar_pasajero.html', {'form': form})

def editar_pasajero(request, pasajero_id):
    pasajero = get_object_or_404(Pasajero, id=pasajero_id)
    if request.method == 'POST':
        form = PasajeroForm(request.POST, instance=pasajero)
        if form.is_valid():
            form.save()
            messages.success(request, "Pasajero actualizado correctamente.")
            return redirect('lista_pasajeros')
    else:
        form = PasajeroForm(instance=pasajero)
    return render(request, 'pasajeros/editar_pasajero.html', {'form': form})

def eliminar_pasajero(request, pasajero_id):
    pasajero = get_object_or_404(Pasajero, id=pasajero_id)
    pasajero.activo = False
    pasajero.save()
    messages.success(request, "Pasajero eliminado correctamente.")
    return redirect('lista_pasajeros')
