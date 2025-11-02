from .repositories import ReporteRepository

class ReporteService:
    @staticmethod
    def obtener_pasajeros_por_vuelo(vuelo_id):
        vuelo, pasajeros = ReporteRepository.obtener_pasajeros_por_vuelo(vuelo_id)
        if not vuelo:
            return None
        return {
            'vuelo': vuelo.codigo_vuelo,
            'origen': vuelo.origen_principal.nombre,
            'destino': vuelo.destino_principal.nombre,
            'pasajeros': [
                {
                    'id': p.id,
                    'nombre': f'{p.persona.nombre} {p.persona.apellido}',
                    'dni': p.persona.dni,
                    'asiento': p.asiento.numero if p.asiento else None,
                }
                for p in pasajeros
            ]
        }

    @staticmethod
    def obtener_reservas_activas_por_pasajero(pasajero_id):
        pasajero, reservas = ReporteRepository.obtener_reservas_activas_por_pasajero(pasajero_id)
        if not pasajero:
            return None
        return {
            'pasajero': f'{pasajero.persona.nombre} {pasajero.persona.apellido}',
            'reservas_activas': [
                {
                    'codigo_reserva': r.codigo,
                    'vuelo': r.vuelo.codigo_vuelo,
                    'fecha_salida': r.vuelo.fecha_salida_estimada,
                    'estado': r.estado,
                }
                for r in reservas
            ]
        }
