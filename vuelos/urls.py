from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LocalidadViewSet, AvionViewSet, EscalaViewSet,
    VueloViewSet, TripulacionVueloViewSet,
    VueloTemplateView, DetailVueloTemplateView
)

router = DefaultRouter()
router.register(r'localidades', LocalidadViewSet)
router.register(r'aviones', AvionViewSet)
router.register(r'escalas', EscalaViewSet)
router.register(r'vuelos', VueloViewSet)
router.register(r'tripulacion', TripulacionVueloViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('vista-vuelos/', VueloTemplateView.as_view(), name='vuelo_template'),
    path('detalle-vuelo/<int:pk>/', DetailVueloTemplateView.as_view(), name='detail_vuelo_template'),

]
