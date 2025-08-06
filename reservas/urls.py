from django.urls import path
from reservas import views

urlpatterns = [
    path('', views.ReservaListView.as_view(), name='reserva_list'),
    path('crear/', views.ReservaCreateView.as_view(), name='crear_reserva'),  
    path('<int:pk>/', views.ReservaDetailView.as_view(), name='reserva_detail'),
    path('<int:pk>/editar/', views.ReservaUpdateView.as_view(), name='reserva_update'),
    path('<int:pk>/eliminar/', views.ReservaDeleteView.as_view(), name='reserva_delete'),
]
