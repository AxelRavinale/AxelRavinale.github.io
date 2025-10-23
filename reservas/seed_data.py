from django.contrib.auth.models import User
from reservas.models import Vuelo, Reserva, Boleto
from django.utils import timezone
import random

def create_seed_data():
    print("Creando datos de prueba...")

    # ==== Usuarios ====
    admin, _ = User.objects.get_or_create(
        username="admin",
        defaults={"email": "admin@aerolinea.com", "is_staff": True, "is_superuser": True}
    )
    admin.set_password("admin123")
    admin.save()

    user1, _ = User.objects.get_or_create(username="danilo", defaults={"email": "danilo@example.com"})
    user1.set_password("1234")
    user1.save()

    user2, _ = User.objects.get_or_create(username="maria", defaults={"email": "maria@example.com"})
    user2.set_password("1234")
    user2.save()

    # ==== Vuelos ====
    vuelos_data = [
        ("Buenos Aires", "Madrid", "2025-10-15 10:00", "2025-10-15 22:00", 250),
        ("Córdoba", "Santiago de Chile", "2025-10-20 08:00", "2025-10-20 11:30", 120),
        ("Buenos Aires", "Miami", "2025-11-01 09:30", "2025-11-01 20:00", 300),
        ("Rosario", "Lima", "2025-11-10 07:00", "2025-11-10 10:30", 180),
    ]

    vuelos_objs = []
    for origen, destino, salida, llegada, precio in vuelos_data:
        vuelo, _ = Vuelo.objects.get_or_create(
            origen=origen,
            destino=destino,
            fecha_salida=salida,
            fecha_llegada=llegada,
            precio=precio,
            capacidad_total=150,
            capacidad_disponible=150,
        )
        vuelos_objs.append(vuelo)

    # ==== Reservas ====
    reservas_objs = []
    for i in range(3):
        reserva, _ = Reserva.objects.get_or_create(
            usuario=random.choice([user1, user2]),
            vuelo=random.choice(vuelos_objs),
            estado="CONFIRMADA",
            fecha_reserva=timezone.now(),
            precio_total=random.randint(100, 500),
        )
        reservas_objs.append(reserva)

    # ==== Boletos ====
    for reserva in reservas_objs:
        Boleto.objects.get_or_create(
            reserva=reserva,
            numero_boleto=f"BO-{random.randint(10000,99999)}",
            asiento=f"{random.randint(1,30)}A",
        )

    print("✅ Datos de prueba creados correctamente.")