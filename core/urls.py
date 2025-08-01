"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language
from .views import PersonaCreateView

urlpatterns = [
    path('set_language/', set_language, name='set_language'),
]

urlpatterns += i18n_patterns(
    path('personas/crear/', PersonaCreateView.as_view(), name='persona_create'),
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('auth/', include('autentificacion.urls')),
    path('', include('vuelos.urls')),
    path('trabajadores/', include('empleados.urls')),
    path('reservas/', include('reservas.urls')),
    path('flota/', include('flota.urls')),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
