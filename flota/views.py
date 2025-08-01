from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Avion
from .forms import AvionForm

def lista_aviones(request):
    aviones = Avion.objects.filter(activo=True)
    return render(request, 'flota/lista_aviones.html', {'aviones': aviones})

def registrar_avion(request):
    if request.method == 'POST':
        form = AvionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Avión registrado correctamente.')
            return redirect('lista_aviones')
    else:
        form = AvionForm()
    return render(request, 'flota/registrar_avion.html', {'form': form})

def editar_avion(request, avion_id):
    avion = get_object_or_404(Avion, id=avion_id)
    if request.method == 'POST':
        form = AvionForm(request.POST, instance=avion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Avión actualizado correctamente.')
            return redirect('lista_aviones')
    else:
        form = AvionForm(instance=avion)
    return render(request, 'flota/editar_avion.html', {'form': form})

def eliminar_avion(request, avion_id):
    avion = get_object_or_404(Avion, id=avion_id)
    avion.activo = False
    avion.save()
    messages.success(request, 'Avión eliminado correctamente.')
    return redirect('lista_aviones')

