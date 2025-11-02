from django.urls import path
from .views import PersonaListCreateAPIView, PersonaRetrieveUpdateDestroyAPIView

urlpatterns = [
    path('personas/', PersonaListCreateAPIView.as_view(), name='persona-list-create'),
    path('personas/<int:pk>/', PersonaRetrieveUpdateDestroyAPIView.as_view(), name='persona-detail'),
]
