from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AvionViewSet

router = DefaultRouter()
router.register(r'aviones', AvionViewSet, basename='avion')

urlpatterns = [
    path('', include(router.urls)),
]
