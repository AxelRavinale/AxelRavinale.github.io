from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/core/', include('core.urls_persona')),        
    path('api/reservas/', include('reservas.urls')),
    path('api/vuelos/', include('vuelos.urls')),
    path('api/flota/', include('flota.urls')),
    path('api/pasajeros/', include('pasajeros.urls')),
    path('api/auth/', include('autentificacion.urls')),   # autenticación con JWT o Token

    path('api/docs/', include('core.swagger_urls')),
]
