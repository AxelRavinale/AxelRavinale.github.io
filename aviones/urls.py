from django.urls import path
from aviones.views import seleccionar_asientos
from django.http import HttpResponse

urlpatterns = [
    path('avion/<int:avion_id>/asientos/', seleccionar_asientos, name='seleccionar_asientos'),
]


def seleccion_exitosa(request):
    return HttpResponse("¡Asientos reservados con éxito!")
