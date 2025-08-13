from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .models import Trabajador
from .forms import UsuarioForm, TrabajadorForm
from django.contrib import messages

def lista_trabajadores(request):
    trabajadores = Trabajador.objects.filter(activo=True)
    return render(request, 'lista_trabajadores.html', {'trabajadores': trabajadores})

def registrar_trabajador(request):
    if request.method == 'POST':
        usuario_form = UsuarioForm(request.POST)
        trabajador_form = TrabajadorForm(request.POST)
        if usuario_form.is_valid() and trabajador_form.is_valid():
            usuario = usuario_form.save(commit=False)
            usuario.set_password(usuario.password)
            usuario.save()
            trabajador = trabajador_form.save(commit=False)
            trabajador.usuario = usuario
            trabajador.save()
            messages.success(request, 'Trabajador registrado correctamente.')
            return redirect('lista_trabajadores')
    else:
        usuario_form = UsuarioForm()
        trabajador_form = TrabajadorForm()
    return render(request, 'registrar_trabajador.html', {
        'usuario_form': usuario_form,
        'trabajador_form': trabajador_form
    })

def eliminar_trabajador(request, trabajador_id):
    trabajador = get_object_or_404(Trabajador, id=trabajador_id)
    trabajador.activo = False
    trabajador.save()
    messages.success(request, 'Trabajador eliminado correctamente.')
    return redirect('lista_trabajadores')

def editar_trabajador(request, trabajador_id):
    trabajador = get_object_or_404(Trabajador, id=trabajador_id)
    usuario = trabajador.usuario

    if request.method == 'POST':
        usuario_form = UsuarioForm(request.POST, instance=usuario)
        trabajador_form = TrabajadorForm(request.POST, instance=trabajador)
        if usuario_form.is_valid() and trabajador_form.is_valid():
            usuario_form.save()
            trabajador_form.save()
            messages.success(request, 'Trabajador actualizado correctamente.')
            return redirect('lista_trabajadores')
    else:
        usuario_form = UsuarioForm(instance=usuario)
        trabajador_form = TrabajadorForm(instance=trabajador)

    return render(request, 'editar_trabajador.html', {
        'usuario_form': usuario_form,
        'trabajador_form': trabajador_form
    })
