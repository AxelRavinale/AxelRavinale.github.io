from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import (
    ReservaSerializer,
    CrearReservaSerializer,
)
from .services import ReservaService


# ==== USUARIOS ====

class VuelosDisponiblesAPI(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        vuelos = ReservaService.listar_vuelos_disponibles()
        data = [{"id": v.id, "origen": v.origen.nombre, "destino": v.destino.nombre, "fecha": v.fecha_salida} for v in vuelos]
        return Response(data)


class CrearReservaAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CrearReservaSerializer(data=request.data)
        if serializer.is_valid():
            try:
                reserva = ReservaService.crear_reserva(
                    serializer.validated_data["pasajero_id"],
                    serializer.validated_data["vuelo_id"],
                    serializer.validated_data["asientos"]
                )
                return Response(ReservaSerializer(reserva).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReservaDetailAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        reserva = ReservaService.obtener_reserva(pk)
        return Response(ReservaSerializer(reserva).data)


class ProcesarPagoAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        reserva = ReservaService.obtener_reserva(pk)
        reserva.estado = "CONFIRMADA"
        reserva.save()
        boleto = ReservaService.generar_boleto(reserva)
        return Response(BoletoSerializer(boleto).data, status=status.HTTP_200_OK)


class CancelarReservaAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        reserva = ReservaService.cambiar_estado(pk, "CANCELADA")
        return Response(ReservaSerializer(reserva).data)


class MisReservasAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        pasajero_id = request.user.id
        reservas = ReservaService.reservas_usuario(pasajero_id)
        return Response(ReservaSerializer(reservas, many=True).data)


# ==== BOLETOS ====

class BoletoDetailAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        from .models import Boleto
        from django.shortcuts import get_object_or_404
        boleto = get_object_or_404(Boleto, pk=pk)
        return Response(BoletoSerializer(boleto).data)


class DescargarBoletoAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        boleto = ReservaService.generar_boleto(ReservaService.obtener_reserva(pk))
        return Response({"mensaje": "Descarga simulada", "codigo": boleto.codigo})


class BuscarBoletoAPI(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from .models import Boleto
        codigo = request.query_params.get("codigo")
        boleto = Boleto.objects.filter(codigo=codigo).first()
        if not boleto:
            return Response({"detail": "Boleto no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        return Response(BoletoSerializer(boleto).data)


# ==== ADMIN ====

class AdminReservasListAPI(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from .models import Reserva
        reservas = Reserva.objects.select_related("vuelo", "pasajero").all()
        return Response(ReservaSerializer(reservas, many=True).data)


class AdminReservaDetailAPI(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, pk):
        reserva = ReservaService.obtener_reserva(pk)
        return Response(ReservaSerializer(reserva).data)


class AdminVueloReservasAPI(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, pk):
        from .repositories import ReservaRepository
        reservas = ReservaRepository.obtener_reservas_vuelo(pk)
        return Response(ReservaSerializer(reservas, many=True).data)
