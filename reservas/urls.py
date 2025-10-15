from django.urls import path
from . import view as views

app_name = "reservas_api"

urlpatterns = [
    # ==== USUARIOS ====
    path("vuelos/", views.VuelosDisponiblesAPI.as_view(), name="vuelos_disponibles"),
    path("reservas/create/", views.CrearReservaAPI.as_view(), name="reserva_create"),
    path("reservas/<int:pk>/", views.ReservaDetailAPI.as_view(), name="reserva_detail"),
    path("reservas/<int:pk>/pagar/", views.ProcesarPagoAPI.as_view(), name="reserva_pagar"),
    path("reservas/<int:pk>/cancelar/", views.CancelarReservaAPI.as_view(), name="reserva_cancelar"),
    path("reservas/mis/", views.MisReservasAPI.as_view(), name="mis_reservas"),

    # ==== BOLETOS ====
    path("boletos/<int:pk>/", views.BoletoDetailAPI.as_view(), name="boleto_detail"),
    path("boletos/<int:pk>/descargar/", views.DescargarBoletoAPI.as_view(), name="boleto_descargar"),
    path("boletos/buscar/", views.BuscarBoletoAPI.as_view(), name="boleto_buscar"),

    # ==== ADMIN ====
    path("admin/reservas/", views.AdminReservasListAPI.as_view(), name="admin_reservas_list"),
    path("admin/reservas/<int:pk>/", views.AdminReservaDetailAPI.as_view(), name="admin_reserva_detail"),
    path("admin/vuelos/<int:pk>/reservas/", views.AdminVueloReservasAPI.as_view(), name="admin_vuelo_reservas"),
]
