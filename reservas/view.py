from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .serializer import (
    ReservaSerializer,
    CrearReservaSerializer,
)
from .services import ReservaService


# ==== USUARIOS ====

class VuelosDisponiblesAPI(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Listar vuelos disponibles",
        description="Obtiene una lista de todos los vuelos disponibles para reservar",
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        vuelos = ReservaService.listar_vuelos_disponibles()
        data = [{"id": v.id, "origen": v.origen_principal.nombre, "destino": v.destino_principal.nombre, "fecha": v.fecha_salida_estimada} for v in vuelos]
        return Response(data)


class CrearReservaAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Crear una nueva reserva",
        description="Crea una reserva con los asientos seleccionados para un vuelo específico",
        request=CrearReservaSerializer,
        responses={
            201: ReservaSerializer,
            400: OpenApiTypes.OBJECT
        }
    )
    @extend_schema(exclude=True)
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

    @extend_schema(
        summary="Obtener detalle de reserva",
        description="Obtiene los detalles de una reserva específica",
        responses={
            200: ReservaSerializer,
            404: OpenApiTypes.OBJECT
        }
    )
    @extend_schema(exclude=True)

    def get(self, request, pk):
        reserva = ReservaService.obtener_reserva(pk)
        return Response(ReservaSerializer(reserva).data)


class ProcesarPagoAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Procesar pago de reserva",
        description="Confirma el pago de una reserva y genera el boleto",
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT
        }
    )
    @extend_schema(exclude=True)
    def post(self, request, pk):
        reserva = ReservaService.obtener_reserva(pk)
        reserva.estado = "CONFIRMADA"
        reserva.save()
        boleto = ReservaService.generar_boleto(reserva)
        # Nota: Necesitas importar BoletoSerializer
        from .serializer import BoletoSerializer
        return Response(BoletoSerializer(boleto).data, status=status.HTTP_200_OK)


class CancelarReservaAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Cancelar una reserva",
        description="Cambia el estado de una reserva a CANCELADA",
        responses={
            200: ReservaSerializer,
            404: OpenApiTypes.OBJECT
        }
    )
    @extend_schema(exclude=True)

    def post(self, request, pk):
        reserva = ReservaService.cambiar_estado(pk, "CANCELADA")
        return Response(ReservaSerializer(reserva).data)


class MisReservasAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Obtener mis reservas",
        description="Lista todas las reservas del usuario autenticado",
        responses={200: ReservaSerializer(many=True)}
    )

    @extend_schema(exclude=True)
    def get(self, request):
        pasajero_id = request.user.id
        reservas = ReservaService.reservas_usuario(pasajero_id)
        return Response(ReservaSerializer(reservas, many=True).data)


# ==== BOLETOS ====

class BoletoDetailAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Obtener detalle de boleto",
        description="Obtiene los detalles de un boleto específico",
        responses={
            200: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        }
    )
    def get(self, request, pk):
        from .models import Boleto
        from .serializer import BoletoSerializer
        from django.shortcuts import get_object_or_404
        boleto = get_object_or_404(Boleto, pk=pk)
        return Response(BoletoSerializer(boleto).data)


class DescargarBoletoAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Descargar boleto",
        description="Genera y descarga el boleto de una reserva",
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        }
    )
    def get(self, request, pk):
        from .models import Boleto, Reserva
        from django.shortcuts import get_object_or_404
        
        # Obtener la reserva
        reserva = get_object_or_404(Reserva, pk=pk)
        
        # Verificar que la reserva esté confirmada
        if reserva.estado != Reserva.EstadoChoices.CONFIRMADA:
            return Response(
                {"error": "La reserva debe estar confirmada para descargar el boleto"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener o crear el boleto
        boleto, created = Boleto.objects.get_or_create(reserva=reserva)
        
        return Response({
            "mensaje": "Descarga simulada",
            "codigo": boleto.codigo_barras,  # ✅ codigo_barras, no codigo
            "codigo_reserva": reserva.codigo_reserva,
            "boleto_id": boleto.id
        })
class BuscarBoletoAPI(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Buscar boleto por código",
        description="Busca un boleto utilizando su código único",
        parameters=[
            OpenApiParameter(
                name='codigo',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Código de barras del boleto',
                required=True
            ),
        ],
        responses={
            200: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        }
    )
    def get(self, request):
        from .models import Boleto
        from .serializer import BoletoSerializer
        codigo = request.query_params.get("codigo")
        
        # Buscar por codigo_barras
        boleto = Boleto.objects.filter(codigo_barras=codigo).first()
        
        if not boleto:
            return Response({"detail": "Boleto no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        return Response(BoletoSerializer(boleto).data)

# ==== ADMIN ====

class AdminReservasListAPI(APIView):
    permission_classes = [permissions.IsAdminUser]

    @extend_schema(
        summary="Listar todas las reservas (Admin)",
        description="Obtiene una lista completa de todas las reservas del sistema",
        responses={200: ReservaSerializer(many=True)}
    )
    def get(self, request):
        from .models import Reserva
        reservas = Reserva.objects.select_related("vuelo", "pasajero").all()
        return Response(ReservaSerializer(reservas, many=True).data)


class AdminReservaDetailAPI(APIView):
    permission_classes = [permissions.IsAdminUser]

    @extend_schema(
        summary="Detalle de reserva (Admin)",
        description="Obtiene los detalles de una reserva específica (solo administradores)",
        responses={
            200: ReservaSerializer,
            404: OpenApiTypes.OBJECT
        }
    )

    @extend_schema(exclude=True)
    def get(self, request, pk):
        reserva = ReservaService.obtener_reserva(pk)
        return Response(ReservaSerializer(reserva).data)


class AdminVueloReservasAPI(APIView):
    
    permission_classes = [permissions.IsAdminUser]

    @extend_schema(exclude=True)
    @extend_schema(
        summary="Reservas de un vuelo (Admin)",
        description="Lista todas las reservas asociadas a un vuelo específico",
        responses={200: ReservaSerializer(many=True)}
    )

    @extend_schema(exclude=True)
    def get(self, request, pk):
        from .repositories import ReservaRepository
        reservas = ReservaRepository.obtener_reservas_vuelo(pk)
        return Response(ReservaSerializer(reservas, many=True).data)