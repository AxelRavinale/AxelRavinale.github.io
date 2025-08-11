from django.urls import path
from reservas import views

urlpatterns = [
    path('', views.ReservaListView.as_view(), name='reserva_list'),
    path('crear/', views.ReservaCreateView.as_view(), name='crear_reserva'),
    path('<int:pk>/', views.ReservaDetailView.as_view(), name='reserva_detail'),
    path('<int:pk>/editar/', views.ReservaUpdateView.as_view(), name='reserva_update'),
    path('<int:pk>/eliminar/', views.ReservaDeleteView.as_view(), name='reserva_delete'),
    path('<int:reserva_pk>/detalles/crear/', views.ReservaDetalleCreateView.as_view(), name='crear_detalle'),
    path('<int:reserva_pk>/detalles/<int:pk>/eliminar/', views.ReservaDetalleDeleteView.as_view(), name='eliminar_detalle'),
]
