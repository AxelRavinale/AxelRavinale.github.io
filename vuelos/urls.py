from django.urls import path, include
from rest_framework.routers import DefaultRouter
from vuelos.views import VueloViewSet, EscalaViewSet, TripulacionVueloViewSet

app_name = 'vuelos'

router = DefaultRouter()
router.register(r'vuelos', VueloViewSet, basename='vuelos')
router.register(r'escalas', EscalaViewSet, basename='escalas')
router.register(r'tripulacion', TripulacionVueloViewSet, basename='tripulacion')

urlpatterns = [
    path('api/', include(router.urls)),
]
