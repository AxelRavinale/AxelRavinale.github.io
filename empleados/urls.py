from django.urls import path
from .views import TrabajadorListCreateAPIView, TrabajadorRetrieveUpdateDestroyAPIView

urlpatterns = [
    path('trabajadores/', TrabajadorListCreateAPIView.as_view(), name='trabajador-list-create'),
    path('trabajadores/<int:pk>/', TrabajadorRetrieveUpdateDestroyAPIView.as_view(), name='trabajador-detail'),
]
