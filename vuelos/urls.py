from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para API REST
router = DefaultRouter()
router.register(r'localidades', views.LocalidadViewSet)
router.register(r'aviones', views.AvionViewSet)
router.register(r'escalas', views.EscalaViewSet)
router.register(r'vuelos', views.VueloViewSet)
router.register(r'tripulacion', views.TripulacionVueloViewSet)

urlpatterns = [
    # API URLs
    path('api/', include(router.urls)),
    
    # Vistas principales
    path('vuelo_list', views.VueloListView.as_view(), name='vuelo_list'),
    path('detalle/<str:codigo_vuelo>/', views.VueloDetailView.as_view(), name='vuelo_detail'),
    
    # FLUJO DE CREACIÓN DE VUELOS (PASO A PASO)
    # Paso 1: Crear vuelo inicial
    path('crear/', views.VueloCreateView.as_view(), name='vuelo_create'),  # CORREGIDO: era 'cargar_vuelo'
    
    # Paso 2A: Gestionar escalas (solo si tiene_escalas=True)
    path('<str:codigo_vuelo>/escalas/', views.VueloEscalasView.as_view(), name='vuelo_escalas'),
    
    # Paso 2B: Gestionar tripulación (solo si tiene_escalas=False)
    path('<str:codigo_vuelo>/tripulacion/', views.VueloTripulacionView.as_view(), name='vuelo_tripulacion'),
    
    # Paso 3: Gestionar tripulación de escalas (para vuelos con escalas)
    path('<str:codigo_vuelo>/tripulacion-escalas/<int:orden>/', views.VueloTripulacionEscalasView.as_view(), name='vuelo_tripulacion_escalas'),

    # Edición
    path('<str:codigo_vuelo>/editar/', views.VueloUpdateView.as_view(), name='update_vuelo'),
    
    # Vistas auxiliares
    path('escala/crear/', views.EscalaCreateView.as_view(), name='escala_create'),
    path('pais/crear/', views.PaisCreateView.as_view(), name='pais_form'),
    path('provincia/crear/', views.ProvinciaCreateView.as_view(), name='provincia_form'),
    path('localidad/crear/', views.LocalidadCreateView.as_view(), name='localidad_create'),
]