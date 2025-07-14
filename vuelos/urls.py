from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para las API Views
router = DefaultRouter()
router.register(r'localidades', views.LocalidadViewSet)
router.register(r'aviones', views.AvionViewSet)
router.register(r'escalas', views.EscalaViewSet)
router.register(r'vuelos', views.VueloViewSet)
router.register(r'tripulacion', views.TripulacionVueloViewSet)

urlpatterns = [
    # URLs de la API REST
    path('api/', include(router.urls)),
    
    # URLs de las vistas template
    path('', views.VueloListView.as_view(), name='vuelo_list'),
    path('template/', views.VueloListView.as_view(), name='vuelo_template'),
    
    # Detalle de vuelo
    path('detalle/<str:codigo_vuelo>/', views.VueloDetailView.as_view(), name='vuelo_detail'),
    path('detalle/<int:pk>/', views.VueloDetailView.as_view(), name='detail_vuelo_template'),
    
    # Crear y editar vuelos
    path('crear/', views.VueloCreateView.as_view(), name='cargar_vuelo'),
    path('editar/<str:codigo_vuelo>/', views.VueloUpdateView.as_view(), name='update_vuelo'),
    
    # Crear escalas independientes
    path('escala/crear/', views.EscalaCreateView.as_view(), name='escala_form'),
    
    # Crear países, provincias y localidades
    path('pais/crear/', views.PaisCreateView.as_view(), name='pais_form'),
    path('provincia/crear/', views.ProvinciaCreateView.as_view(), name='provincia_form'),
    path('localidad/crear/', views.LocalidadCreateView.as_view(), name='localidad_form'),
    
    # Vista adicional (si la necesitas)
    path('listar/', views.listar_vuelos, name='listar_vuelos'),
]