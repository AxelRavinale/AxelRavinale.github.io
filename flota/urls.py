from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_aviones, name='lista_aviones'),
    path('registrar/', views.registrar_avion, name='registrar_avion'),
    path('editar/<int:avion_id>/', views.editar_avion, name='editar_avion'),
    path('eliminar/<int:avion_id>/', views.eliminar_avion, name='eliminar_avion'),
]
