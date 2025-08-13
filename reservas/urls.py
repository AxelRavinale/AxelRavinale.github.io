from django.urls import path
from . import views

app_name = 'reservas'

urlpatterns = [
    # Redirección desde home
    path('', views.HomeRedirectView.as_view(), name='home_redirect'),
    
    # RUTAS PARA ADMINISTRADORES
    path('admin/', views.AdminInicioView.as_view(), name='admin_inicio'),
    path('admin/crear-reserva/', views.AdminCrearReservaView.as_view(), name='admin_crear_reserva'),
    path('admin/configuracion-vuelo/<int:pk>/', views.AdminConfiguracionVueloView.as_view(), name='admin_configuracion_vuelo'),
    path('admin/reservas/', views.AdminReservasListView.as_view(), name='admin_reservas_list'),
    path('admin/reserva/<int:pk>/', views.AdminReservaDetailView.as_view(), name='admin_reserva_detail'),
    path('admin/vuelo/<int:pk>/reservas/', views.AdminVueloReservasView.as_view(), name='admin_vuelo_reservas'),
    
    # RUTAS PARA USUARIOS NORMALES
    path('user/', views.UserInicioView.as_view(), name='user_inicio'),
    path('vuelos-disponibles/', views.VuelosDisponiblesView.as_view(), name='vuelos_disponibles'),
    path('seleccion-asientos/<int:pk>/', views.SeleccionAsientosView.as_view(), name='seleccion_asientos'),
    path('confirmar-reserva/<int:pk>/', views.ConfirmarReservaView.as_view(), name='confirmar_reserva'),
    path('procesar-pago/<int:pk>/', views.ProcesarPagoView.as_view(), name='procesar_pago'),
    path('reserva-confirmada/<int:pk>/', views.ReservaConfirmadaView.as_view(), name='reserva_confirmada'),
    path('mis-reservas/', views.MisReservasView.as_view(), name='mis_reservas'),
    path('reserva/<int:pk>/', views.ReservaDetailUserView.as_view(), name='reserva_detail_user'),
    
    # RUTAS PARA BOLETOS
    path('boleto/<int:pk>/', views.BoletoDetailView.as_view(), name='boleto_detail'),
    path('buscar-boleto/', views.BuscarBoletoView.as_view(), name='buscar_boleto'),
    path('boleto-publico/<int:pk>/', views.BoletoPublicoView.as_view(), name='boleto_publico'),
    path('descargar-boleto/<int:pk>/', views.DescargarBoletoView.as_view(), name='descargar_boleto'),
    path('descargar-detalle/<int:pk>/', views.DescargarDetalleReservaView.as_view(), name='descargar_detalle_reserva'),
]