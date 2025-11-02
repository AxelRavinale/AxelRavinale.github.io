from django.shortcuts import get_object_or_404
from .models import Reserva, AsientoVuelo, Boleto
from .repositories import ReservaRepository
from vuelos.models import Vuelo
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class ReservaService:

    @staticmethod
    def listar_reservas():
        return ReservaRepository.obtener_reservas()

    @staticmethod
    def obtener_reserva(reserva_id):
        return ReservaRepository.obtener_por_id(reserva_id)

    @staticmethod
    def crear_reserva(pasajero_id, vuelo_id, asientos_ids):
        """
        Crea una reserva
        pasajero_id: ID del User (pasajero)
        vuelo_id: ID del Vuelo
        asientos_ids: lista de IDs de AsientoVuelo
        """
        pasajero = get_object_or_404(User, id=pasajero_id)
        vuelo = get_object_or_404(Vuelo, id=vuelo_id)
        
        # Obtener los AsientoVuelo (NO Asiento directamente)
        asientos_vuelo = AsientoVuelo.objects.filter(
            id__in=asientos_ids,
            vuelo=vuelo,
            habilitado_para_reserva=True,
            activo=True
        )
        
        if not asientos_vuelo.exists():
            raise ValidationError("No se encontraron asientos válidos para este vuelo")
        
        if asientos_vuelo.count() != len(asientos_ids):
            raise ValidationError("Algunos asientos no son válidos o no están disponibles")
        
        # Verificar que ningún asiento esté ya reservado
        for asiento_vuelo in asientos_vuelo:
            if asiento_vuelo.esta_reservado:
                raise ValidationError(f"El asiento {asiento_vuelo.asiento.numero} ya está reservado")
        
        # Calcular precio total (suma de precios de cada AsientoVuelo)
        precio_total = sum(av.precio for av in asientos_vuelo)
        
        # Crear la reserva
        reserva = ReservaRepository.crear_reserva(
            pasajero=pasajero,
            vuelo=vuelo,
            asientos_vuelo=list(asientos_vuelo),
            precio_total=precio_total
        )
        
        return reserva

    @staticmethod
    def cambiar_estado(reserva_id, nuevo_estado):
        reserva = ReservaRepository.obtener_por_id(reserva_id)
        return ReservaRepository.actualizar_estado(reserva, nuevo_estado)

    @staticmethod
    def listar_vuelos_disponibles():
        """Lista vuelos que tienen asientos configurados y disponibles"""
        from .models import ConfiguracionVuelo
        configuraciones = ConfiguracionVuelo.objects.filter(
            configurado=True,
            vuelo__activo=True
        ).select_related('vuelo')
        return [c.vuelo for c in configuraciones]

    @staticmethod
    def reservas_usuario(pasajero_id):
        """Obtiene todas las reservas de un usuario"""
        return ReservaRepository.obtener_reservas_pasajero(pasajero_id)
    
    @staticmethod
    def generar_boleto(reserva):
        """Genera un boleto para una reserva confirmada"""
        # Verificar si ya tiene boleto
        if hasattr(reserva, 'boleto'):
            return reserva.boleto
        
        # Crear nuevo boleto (el modelo ya maneja la generación de código y snapshots)
        boleto = Boleto.objects.create(reserva=reserva)
        return boleto