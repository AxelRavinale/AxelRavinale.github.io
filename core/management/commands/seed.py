from django.core.management.base import BaseCommand
from datetime import datetime, timedelta, date
from decimal import Decimal
import random
from django.utils import timezone

from django.contrib.auth.models import User
from core.models import Pais, Provincia, Localidad, Genero, TipoDocumento, Persona, TipoVuelo, Estado
from aviones.models import Avion, Asiento
from empleados.models import Trabajador
from pasajeros.models import Pasajero
from vuelos.models import Escala, Vuelo, EscalaVuelo, TripulacionVuelo, TripulacionEscala
from reservas.models import Reserva, ReservaDetalle, AsientoVuelo


class Command(BaseCommand):
    help = 'Carga datos de prueba para el sistema de gestión de vuelos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpia todos los datos antes de cargar',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando seed de datos...'))

        if options['clear']:
            self.clear_data()

        self.create_core_data()
        self.create_users_and_personas()
        self.create_trabajadores()
        self.create_pasajeros()
        self.create_aviones()
        self.create_escalas()
        self.create_vuelos()
        self.create_configuracion_asientos()
        self.create_tripulacion()
        self.create_reservas()
        
        self.print_summary()

    def clear_data(self):
        self.stdout.write('🗑️  Limpiando datos existentes...')
        ReservaDetalle.objects.all().delete()
        Reserva.objects.all().delete()
        AsientoVuelo.objects.all().delete()
        TripulacionEscala.objects.all().delete()
        TripulacionVuelo.objects.all().delete()
        EscalaVuelo.objects.all().delete()
        Vuelo.objects.all().delete()
        Escala.objects.all().delete()
        Asiento.objects.all().delete()
        Avion.objects.all().delete()
        Pasajero.objects.all().delete()
        Trabajador.objects.all().delete()
        Persona.objects.all().delete()
        Localidad.objects.all().delete()
        Provincia.objects.all().delete()
        Pais.objects.all().delete()
        Genero.objects.all().delete()
        TipoDocumento.objects.all().delete()
        TipoVuelo.objects.all().delete()
        Estado.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

    def create_core_data(self):
        self.stdout.write('📍 Creando datos de Core...')
        
        # Géneros
        generos_data = ['Masculino', 'Femenino', 'No binario', 'Prefiero no decir']
        self.generos = [Genero.objects.create(nombre=g, activo=True) for g in generos_data]
        
        # Tipos de Documento
        tipos_doc_data = ['DNI', 'Pasaporte', 'Cédula', 'Licencia de Conducir']
        self.tipos_documento = [TipoDocumento.objects.create(nombre=td, activo=True) for td in tipos_doc_data]
        
        # Países
        paises_data = ['Argentina', 'Brasil', 'Chile', 'Uruguay', 'Paraguay',
                      'Colombia', 'Perú', 'Bolivia', 'Ecuador', 'Venezuela',
                      'México', 'España', 'Estados Unidos']
        self.paises = {nombre: Pais.objects.create(nombre=nombre, activo=True) for nombre in paises_data}
        
        # Provincias
        provincias_data = {
            'Argentina': ['Buenos Aires', 'Córdoba', 'Santa Fe', 'Mendoza', 'Tucumán', 'Salta'],
            'Brasil': ['São Paulo', 'Río de Janeiro', 'Brasilia', 'Minas Gerais'],
            'Chile': ['Santiago', 'Valparaíso', 'Concepción', 'Antofagasta'],
            'Uruguay': ['Montevideo', 'Canelones', 'Maldonado'],
            'Colombia': ['Bogotá', 'Medellín', 'Cali', 'Cartagena'],
            'México': ['Ciudad de México', 'Jalisco', 'Nuevo León'],
            'España': ['Madrid', 'Barcelona', 'Valencia', 'Sevilla'],
            'Estados Unidos': ['California', 'Nueva York', 'Florida', 'Texas']
        }
        
        self.provincias = {}
        for pais_nombre, provs in provincias_data.items():
            for prov_nombre in provs:
                prov = Provincia.objects.create(pais=self.paises[pais_nombre], nombre=prov_nombre, activo=True)
                self.provincias[f"{pais_nombre}-{prov_nombre}"] = prov
        
        # Localidades
        localidades_data = {
            'Argentina-Buenos Aires': ['Buenos Aires', 'La Plata', 'Mar del Plata', 'Bahía Blanca'],
            'Argentina-Córdoba': ['Córdoba', 'Río Cuarto', 'Villa María', 'Carlos Paz'],
            'Argentina-Santa Fe': ['Rosario', 'Santa Fe', 'Rafaela'],
            'Argentina-Mendoza': ['Mendoza', 'San Rafael', 'Godoy Cruz'],
            'Brasil-São Paulo': ['São Paulo', 'Campinas', 'Santos'],
            'Brasil-Río de Janeiro': ['Río de Janeiro', 'Niterói'],
            'Chile-Santiago': ['Santiago', 'Pudahuel', 'Maipú'],
            'Uruguay-Montevideo': ['Montevideo', 'Ciudad Vieja'],
            'Colombia-Bogotá': ['Bogotá', 'Soacha'],
            'México-Ciudad de México': ['Ciudad de México', 'Ecatepec'],
            'España-Madrid': ['Madrid', 'Alcalá de Henares'],
            'España-Barcelona': ['Barcelona', 'Badalona'],
            'Estados Unidos-California': ['Los Ángeles', 'San Francisco', 'San Diego'],
            'Estados Unidos-Nueva York': ['Nueva York', 'Buffalo']
        }
        
        self.localidades = {}
        for prov_key, locs in localidades_data.items():
            for loc_nombre in locs:
                loc = Localidad.objects.create(provincia=self.provincias[prov_key], nombre=loc_nombre, activo=True)
                self.localidades[loc_nombre] = loc
        
        # Tipos de Vuelo y Estados
        tipos_vuelo_data = ['Nacional', 'Internacional', 'Regional', 'Chárter']
        [TipoVuelo.objects.create(name=tv, activo=True) for tv in tipos_vuelo_data]
        
        estados_data = ['Programado', 'En Vuelo', 'Completado', 'Cancelado', 'Demorado']
        self.estados = {nombre: Estado.objects.create(nombre=nombre) for nombre in estados_data}

    def create_users_and_personas(self):
        self.stdout.write('👥 Creando Usuarios y Personas...')
        
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@vuelos.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('  ✓ Superusuario creado: admin / admin123'))
        
        self.personas = []
        self.usuarios_pasajeros = []
        
        nombres = ['Juan', 'María', 'Carlos', 'Ana', 'Luis', 'Laura', 'Pedro', 'Sofía', 'Diego', 'Valentina',
                   'Miguel', 'Camila', 'Jorge', 'Lucía', 'Roberto', 'Paula', 'Fernando', 'Victoria']
        apellidos = ['García', 'Rodríguez', 'Martínez', 'López', 'González', 'Pérez', 'Sánchez', 'Ramírez']
        
        for i in range(15):
            nombre = random.choice(nombres)
            apellido = random.choice(apellidos)
            username = f"{nombre.lower()}{apellido.lower()}{i+1}"
            
            # Verificar si el usuario ya existe
            if User.objects.filter(username=username).exists():
                user = User.objects.get(username=username)
                self.stdout.write(f"  ⚠ Usuario {username} ya existe, usando existente...")
            else:
                user = User.objects.create_user(
                    username=username,
                    email=f"{username}@email.com",
                    password='password123',
                    first_name=nombre,
                    last_name=apellido
                )
            self.usuarios_pasajeros.append(user)
            
            # Verificar si la persona ya existe
            if not Persona.objects.filter(user=user).exists():
                persona = Persona.objects.create(
                    user=user,
                    nombre=nombre,
                    apellido=apellido,
                    tipo_documento=random.choice(['DNI', 'Pasaporte', 'Cédula']),
                    numero_documento=f"{20000000 + i}{random.randint(100, 999)}",
                    fecha_nacimiento=date(random.randint(1970, 2000), random.randint(1, 12), random.randint(1, 28)),
                    localidad=random.choice(list(self.localidades.values())).nombre,
                    email=f"{username}@email.com",
                    genero=random.choice(['Masculino', 'Femenino']),
                    activo=True
                )
                self.personas.append(persona)
            else:
                persona = Persona.objects.get(user=user)
                self.personas.append(persona)

    def create_trabajadores(self):
        self.stdout.write('👔 Creando Trabajadores...')
        self.trabajadores = []
        cargos = ['Piloto', 'Copiloto', 'Azafata', 'Sobrecargo', 'Técnico de Mantenimiento']
        
        nombres = ['Roberto', 'Carmen', 'Javier', 'Isabel', 'Marcos', 'Daniela', 'Alberto', 'Patricia']
        apellidos = ['Silva', 'Moreno', 'Castro', 'Ortiz', 'Ruiz', 'Vega']
        
        for i in range(10):
            nombre = random.choice(nombres)
            apellido = random.choice(apellidos)
            username = f"trabajador{i+1}"
            
            if User.objects.filter(username=username).exists():
                self.stdout.write(f"  ⚠ Usuario {username} ya existe, saltando...")
                user = User.objects.get(username=username)
                if Trabajador.objects.filter(usuario=user).exists():
                    self.trabajadores.append(Trabajador.objects.get(usuario=user))
                continue
            
            user = User.objects.create_user(
                username=username,
                email=f"{username}@vuelos.com",
                password='password123',
                first_name=nombre,
                last_name=apellido
            )
            
            trabajador = Trabajador.objects.create(
                usuario=user,
                dni=f"{30000000 + i}",
                cargo=random.choice(cargos),
                telefono=f"+549351{random.randint(1000000, 9999999)}",
                fecha_ingreso=date(random.randint(2018, 2023), random.randint(1, 12), 1),
                activo=True
            )
            self.trabajadores.append(trabajador)

    def create_pasajeros(self):
        self.stdout.write('🧳 Creando Pasajeros...')
        self.pasajeros_obj = []
        
        nombres = ['Ricardo', 'Gabriela', 'Martín', 'Claudia', 'Sergio', 'Mónica', 'Pablo', 'Andrea']
        apellidos = ['Fernández', 'Jiménez', 'Núñez', 'Romero', 'Medina', 'Aguilar']
        
        for i in range(12):
            nombre = random.choice(nombres)
            apellido = random.choice(apellidos)
            dni = f"{25000000 + i}{random.randint(10, 99)}"
            
            # Verificar si ya existe
            if Pasajero.objects.filter(dni=dni).exists():
                pasajero = Pasajero.objects.get(dni=dni)
            else:
                pasajero = Pasajero.objects.create(
                    nombre=nombre,
                    apellido=apellido,
                    dni=dni,
                    email=f"pasajero{i+1}@email.com",
                    telefono=f"+549351{random.randint(1000000, 9999999)}",
                    activo=True
                )
            self.pasajeros_obj.append(pasajero)

    def create_aviones(self):
        self.stdout.write('✈️  Creando Aviones...')
        self.aviones = []
        modelos = [
            ('Boeing', '737-800', 189),
            ('Boeing', '777-300ER', 350),
            ('Airbus', 'A320neo', 180),
            ('Airbus', 'A350-900', 325),
            ('Embraer', 'E195', 120),
            ('Boeing', '787-9', 290),
            ('Airbus', 'A330-300', 277),
            ('Boeing', '737 MAX 8', 178),
            ('Airbus', 'A321neo', 220),
            ('Embraer', 'E190', 114),
        ]
        
        for i, (fabricante, modelo, capacidad) in enumerate(modelos):
            num_avion = f"AV{1000 + i}"
            
            # Verificar si ya existe
            if Avion.objects.filter(num_avion=num_avion).exists():
                avion = Avion.objects.get(num_avion=num_avion)
                self.stdout.write(f"  ⚠ Avión {num_avion} ya existe, usando existente...")
            else:
                filas = capacidad // 6
                columnas = 6
                
                avion = Avion.objects.create(
                    num_avion=num_avion,
                    modelo=f"{fabricante} {modelo}",
                    filas=filas,
                    columnas=columnas,
                    estado='operativo',
                    km_recorridos=random.randint(50000, 500000),
                    activo=True
                )
                
                self.stdout.write(f"  → Generando asientos para {avion.num_avion}")
                avion.generar_asientos()
            
            self.aviones.append(avion)

    def create_escalas(self):
        self.stdout.write('🛫 Creando Escalas...')
        self.escalas = []
        rutas_escalas = [
            ('Buenos Aires', 'Córdoba', 700),
            ('Córdoba', 'Mendoza', 600),
            ('Buenos Aires', 'Rosario', 300),
            ('Santiago', 'Buenos Aires', 1400),
            ('São Paulo', 'Río de Janeiro', 430),
            ('Montevideo', 'Buenos Aires', 230),
            ('Bogotá', 'Medellín', 380),
            ('Madrid', 'Barcelona', 620),
            ('Ciudad de México', 'Los Ángeles', 2500),
            ('Nueva York', 'Los Ángeles', 4500),
            ('Buenos Aires', 'Santiago', 1400),
            ('Córdoba', 'Santiago', 900),
        ]
        
        for origen_nombre, destino_nombre, km in rutas_escalas:
            if origen_nombre in self.localidades and destino_nombre in self.localidades:
                # Verificar si ya existe
                if Escala.objects.filter(
                    origen=self.localidades[origen_nombre],
                    destino=self.localidades[destino_nombre]
                ).exists():
                    escala = Escala.objects.get(
                        origen=self.localidades[origen_nombre],
                        destino=self.localidades[destino_nombre]
                    )
                else:
                    escala = Escala.objects.create(
                        origen=self.localidades[origen_nombre],
                        destino=self.localidades[destino_nombre],
                        km_estimados=km,
                        activo=True
                    )
                self.escalas.append(escala)

    def create_vuelos(self):
        self.stdout.write('🛩️  Creando Vuelos...')
        self.vuelos = []
        codigos_aerolinea = ['AR', 'LA', 'AV', 'CM', 'IB', 'UA']
        
        # Vuelos directos
        self.stdout.write('  → Vuelos directos')
        for i in range(8):
            codigo = f"{random.choice(codigos_aerolinea)}{1000 + i}"
            
            # Verificar si ya existe
            if Vuelo.objects.filter(codigo_vuelo=codigo).exists():
                vuelo = Vuelo.objects.get(codigo_vuelo=codigo)
                self.stdout.write(f"  ⚠ Vuelo {codigo} ya existe, usando existente...")
            else:
                origen = random.choice(list(self.localidades.values()))
                destino = random.choice([l for l in self.localidades.values() if l != origen])
                
                fecha_salida = timezone.now() + timedelta(days=random.randint(1, 60), hours=random.randint(6, 22))
                duracion = timedelta(hours=random.randint(1, 8))
                fecha_llegada = fecha_salida + duracion
                
                vuelo = Vuelo.objects.create(
                    codigo_vuelo=codigo,
                    origen_principal=origen,
                    destino_principal=destino,
                    fecha_salida_estimada=fecha_salida,
                    fecha_llegada_estimada=fecha_llegada,
                    km_totales=random.randint(300, 3000),
                    avion_asignado=random.choice(self.aviones),
                    tiene_escalas=False,
                    activo=True,
                    cargado_por=User.objects.first()
                )
            self.vuelos.append(vuelo)
        
        # Vuelos con escalas
        self.stdout.write('  → Vuelos con escalas')
        for i in range(5):
            codigo = f"{random.choice(codigos_aerolinea)}{2000 + i}"
            
            if Vuelo.objects.filter(codigo_vuelo=codigo).exists():
                vuelo = Vuelo.objects.get(codigo_vuelo=codigo)
                self.stdout.write(f"  ⚠ Vuelo {codigo} ya existe, usando existente...")
            else:
                origen = self.localidades['Buenos Aires']
                destino = self.localidades['Santiago']
                
                fecha_salida = timezone.now() + timedelta(days=random.randint(1, 60), hours=random.randint(6, 22))
                fecha_llegada = fecha_salida + timedelta(hours=random.randint(4, 10))
                
                vuelo = Vuelo.objects.create(
                    codigo_vuelo=codigo,
                    origen_principal=origen,
                    destino_principal=destino,
                    fecha_salida_estimada=fecha_salida,
                    fecha_llegada_estimada=fecha_llegada,
                    km_totales=2100,
                    avion_asignado=random.choice(self.aviones),
                    tiene_escalas=True,
                    activo=True,
                    cargado_por=User.objects.first()
                )
                
                # Agregar escalas
                escala1 = [e for e in self.escalas if e.origen.nombre == 'Buenos Aires' and e.destino.nombre == 'Córdoba']
                escala2 = [e for e in self.escalas if e.origen.nombre == 'Córdoba' and e.destino.nombre == 'Santiago']
                
                if escala1 and escala2:
                    fecha_actual = fecha_salida
                    
                    EscalaVuelo.objects.create(
                        vuelo=vuelo,
                        escala=escala1[0],
                        orden=1,
                        fecha_salida=fecha_actual,
                        fecha_llegada=fecha_actual + timedelta(hours=2),
                        avion=vuelo.avion_asignado,
                        activo=True
                    )
                    
                    fecha_actual += timedelta(hours=2.5)
                    
                    EscalaVuelo.objects.create(
                        vuelo=vuelo,
                        escala=escala2[0],
                        orden=2,
                        fecha_salida=fecha_actual,
                        fecha_llegada=fecha_actual + timedelta(hours=2),
                        avion=vuelo.avion_asignado,
                        activo=True
                    )
            
            self.vuelos.append(vuelo)

    def create_configuracion_asientos(self):
        self.stdout.write('💺 Configurando asientos para vuelos...')
        
        tipos_asiento = ['ECO', 'PRE', 'EJE', 'PRI']
        precios_base = {
            'ECO': Decimal('15000'),
            'PRE': Decimal('25000'),
            'EJE': Decimal('40000'),
            'PRI': Decimal('60000')
        }
        
        for vuelo in self.vuelos[:10]:  # Configurar solo los primeros 10 vuelos
            if not vuelo.tiene_escalas:
                # Vuelo directo
                if vuelo.avion_asignado:
                    asientos = vuelo.avion_asignado.asientos.filter(activo=True)[:30]  # Limitamos a 30 asientos
                    
                    for asiento in asientos:
                        tipo = random.choice(tipos_asiento)
                        precio = precios_base[tipo] * Decimal(str(random.uniform(0.8, 1.2)))
                        
                        AsientoVuelo.objects.get_or_create(
                            vuelo=vuelo,
                            asiento=asiento,
                            defaults={
                                'tipo_asiento': tipo,
                                'precio': precio,
                                'habilitado_para_reserva': True,
                                'activo': True,
                                'configurado_por': User.objects.first()
                            }
                        )
                    
                    self.stdout.write(f"  ✓ Configurados {asientos.count()} asientos para {vuelo.codigo_vuelo}")

    def create_tripulacion(self):
        self.stdout.write('👨‍✈️ Asignando Tripulación...')
        roles = ['piloto', 'copiloto', 'azafata', 'sobrecargo']
        
        for vuelo in self.vuelos[:10]:
            if not vuelo.tiene_escalas:
                personas_asignadas = random.sample(self.personas, min(4, len(self.personas)))
                for idx, persona in enumerate(personas_asignadas):
                    TripulacionVuelo.objects.get_or_create(
                        vuelo=vuelo,
                        persona=persona,
                        rol=roles[idx % len(roles)],
                        defaults={'activo': True}
                    )

    def create_reservas(self):
        self.stdout.write('🎫 Creando Reservas...')
        
        vuelos_configurados = []
        for vuelo in self.vuelos:
            if AsientoVuelo.objects.filter(vuelo=vuelo, activo=True).exists():
                vuelos_configurados.append(vuelo)
        
        if not vuelos_configurados:
            self.stdout.write(self.style.WARNING('  ⚠ No hay vuelos con asientos configurados. Saltando reservas.'))
            return
        
        for i in range(min(15, len(self.usuarios_pasajeros))):
            vuelo = random.choice(vuelos_configurados)
            usuario = self.usuarios_pasajeros[i % len(self.usuarios_pasajeros)]
            
            # Obtener asientos disponibles
            asientos_disponibles = AsientoVuelo.objects.filter(
                vuelo=vuelo,
                activo=True,
                habilitado_para_reserva=True
            ).exclude(
                reservadetalle__reserva__estado__in=['CON', 'RSP', 'CRE'],
                reservadetalle__reserva__activo=True
            )[:random.randint(1, 2)]
            
            if not asientos_disponibles:
                continue
            
            # Crear reserva
            reserva = Reserva.objects.create(
                pasajero=usuario,
                vuelo=vuelo,
                estado='CRE',
                activo=True
            )
            
            # Asignar asientos
            for asiento_vuelo in asientos_disponibles:
                ReservaDetalle.objects.create(
                    reserva=reserva,
                    asiento_vuelo=asiento_vuelo,
                    precio_pagado=asiento_vuelo.precio
                )
            
            reserva.calcular_precio_total()
            self.stdout.write(f"  ✓ Reserva {reserva.codigo_reserva} creada ({reserva.get_estado_display()})")

    def print_summary(self):
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('✅ SEED COMPLETADO'))
        self.stdout.write('='*50)
        self.stdout.write(f"📊 Estadísticas:")
        self.stdout.write(f"  • Países: {Pais.objects.count()}")
        self.stdout.write(f"  • Provincias: {Provincia.objects.count()}")
        self.stdout.write(f"  • Localidades: {Localidad.objects.count()}")
        self.stdout.write(f"  • Personas: {Persona.objects.count()}")
        self.stdout.write(f"  • Usuarios: {User.objects.count()}")
        self.stdout.write(f"  • Trabajadores: {Trabajador.objects.count()}")
        self.stdout.write(f"  • Pasajeros: {Pasajero.objects.count()}")
        self.stdout.write(f"  • Aviones: {Avion.objects.count()}")
        self.stdout.write(f"  • Asientos: {Asiento.objects.count()}")
        self.stdout.write(f"  • Escalas: {Escala.objects.count()}")
        self.stdout.write(f"  • Vuelos: {Vuelo.objects.count()}")
        self.stdout.write(f"  • Asientos configurados: {AsientoVuelo.objects.count()}")
        self.stdout.write(f"  • Reservas: {Reserva.objects.count()}")
        self.stdout.write(f"  • Detalles de Reserva: {ReservaDetalle.objects.count()}")
        self.stdout.write('\n🔐 Credenciales:')
        self.stdout.write('  Admin: admin / admin123')
        self.stdout.write('  Usuarios: [nombre][apellido][número] / password123')
        self.stdout.write('  Ejemplo: juangarcia1 / password123')
        self.stdout.write('='*50)