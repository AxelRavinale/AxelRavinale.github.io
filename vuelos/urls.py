from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LocalidadViewSet, AvionViewSet, EscalaViewSet,
    VueloViewSet, TripulacionVueloViewSet
)

router = DefaultRouter()
router.register(r'localidades', LocalidadViewSet)
router.register(r'aviones', AvionViewSet)
router.register(r'escalas', EscalaViewSet)
router.register(r'vuelos', VueloViewSet)
router.register(r'tripulacion', TripulacionVueloViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
