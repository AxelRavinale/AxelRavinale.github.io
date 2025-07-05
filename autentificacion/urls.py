from django.urls import path
from autentificacion.views import RegisterView, LoginView, logout_view, change_language

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('language/<str:lang_code>/', change_language, name='change_language')
]