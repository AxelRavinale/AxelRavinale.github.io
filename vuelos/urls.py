from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LocalidadViewSet, AvionViewSet, EscalaViewSet,
    VueloViewSet, TripulacionVueloViewSet,
    VueloTemplateView, DetailVueloTemplateView,
    VueloCreateView, EscalaCreateView,
    LocalidadCreateView,
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
    path('cargar-vuelo/', VueloCreateView.as_view(), name='cargar_vuelo'),
    path('cargar-escala/', EscalaCreateView.as_view(), name='escala_create'),
     path('cargar-localidad/', LocalidadCreateView.as_view(), name='localidad_create'),
]
