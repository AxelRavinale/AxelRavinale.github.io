from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/core/', include('core.urls_persona')),        
    path('api/reservas/', include('reservas.urls')),
    path('api/vuelos/', include('vuelos.urls')),
    path('api/flota/', include('flota.urls')),
    path('api/pasajeros/', include('pasajeros.urls')),
    path('api/auth/', include('autentificacion.urls')),   # autenticación con JWT o Token

    path('api/docs/', include('core.swagger_urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
