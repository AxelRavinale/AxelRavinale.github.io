from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_pasajeros, name='lista_pasajeros'),
    path('registrar/', views.registrar_pasajero, name='registrar_pasajero'),
    path('editar/<int:pasajero_id>/', views.editar_pasajero, name='editar_pasajero'),
    path('eliminar/<int:pasajero_id>/', views.eliminar_pasajero, name='eliminar_pasajero'),
]
