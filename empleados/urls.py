from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_trabajadores, name='lista_trabajadores'),
    path('registrar/', views.registrar_trabajador, name='registrar_trabajador'),
    path('eliminar/<int:trabajador_id>/', views.eliminar_trabajador, name='eliminar_trabajador'),
    path('editar/<int:trabajador_id>/', views.editar_trabajador, name='editar_trabajador'),
]
