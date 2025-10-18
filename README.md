# Sistema de Gestión de Aerolínea ✈️

Un sistema web completo desarrollado en Django para la gestión integral de una aerolínea, incluyendo reservas, vuelos, pasajeros, empleados y flota de aviones.

## 🚀 Características Principales

### Para Pasajeros
- **Búsqueda de vuelos** disponibles por fecha y destino
- **Selección de asientos** interactiva con mapa visual del avión
- **Gestión de reservas** - crear, consultar y administrar reservas
- **Sistema de pagos** con fechas límite y estados de pago
- **Consulta pública de boletos** mediante código de reserva
- **Panel personal** para ver historial de reservas

### Para Administradores
- **Gestión de vuelos** - crear, modificar y programar vuelos
- **Administración de escalas** para vuelos con paradas intermedias
- **Gestión de tripulación** - asignar pilotos y personal de cabina
- **Control de flota** - registro y mantenimiento de aviones
- **Gestión de empleados** - alta, baja y modificación de personal
- **Administración de pasajeros** - registro y actualización de datos
- **Configuración de asientos** por tipo de avión
- **Sistema de reservas administrativas** para agencias

## 🏗️ Arquitectura del Sistema

El proyecto está organizado en aplicaciones modulares de Django:

```
├── autentificacion/     # Sistema de login y registro
├── aviones/            # Gestión de flota y asientos
├── core/               # Modelos base y configuración
├── empleados/          # Administración de personal
├── flota/              # Gestión de aviones
├── home/               # Página principal
├── pasajeros/          # Gestión de pasajeros
├── reservas/           # Sistema de reservas y boletos
└── vuelos/             # Programación y gestión de vuelos
```

## 📋 Requisitos del Sistema

- Python 3.10+
- Django 4.x
- SQLite (incluido) o PostgreSQL para producción
- Dependencias listadas en `requirements.txt`

## 🛠️ Instalación

1. **Clonar el repositorio**
```bash
git clone <url-del-repositorio>
cd sistema-aerolinea
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar base de datos**
```bash
python manage.py migrate
```

5. **Crear superusuario**
```bash
python manage.py createsuperuser
```

6. **Ejecutar servidor de desarrollo**
```bash
python manage.py runserver
```

El sistema estará disponible en `http://localhost:8000`

## 🗄️ Modelos de Datos Principales

### Estructura de Vuelos
- **Vuelo**: Información básica del vuelo (número, origen, destino, fechas)
- **Escala**: Paradas intermedias con tiempos de conexión
- **TripulacionVuelo**: Asignación de personal (pilotos, azafatas)

### Sistema de Reservas
- **Reserva**: Reserva principal con estado de pago
- **ReservaDetalle**: Detalles específicos por pasajero
- **Boleto**: Boleto individual vinculado a asiento específico
- **AsientoVuelo**: Configuración de asientos por vuelo

### Gestión de Personal
- **Empleado**: Datos del personal de la aerolínea
- **Pasajero**: Información de pasajeros registrados
- **Persona**: Modelo base con datos personales

### Flota
- **Avion**: Información de la aeronave
- **Asiento**: Configuración de asientos por avión (clase, ubicación)

## 🌐 Internacionalización

El sistema soporta múltiples idiomas:
- **Español** (es) - Idioma principal
- **Inglés** (en) - Idioma secundario

Los archivos de traducción se encuentran en el directorio `locale/`.

## 📱 Interfaces de Usuario

### Panel de Administración
- Interfaz administrativa completa de Django
- Gestión de todos los modelos del sistema
- Reportes y estadísticas

### Interfaz Pública
- **Búsqueda de vuelos**: Formulario intuitivo con filtros
- **Selección de asientos**: Mapa visual interactivo del avión
- **Proceso de reserva**: Flujo paso a paso
- **Consulta de boletos**: Búsqueda por código de reserva

### Panel de Usuario
- **Mis reservas**: Historial completo de reservas
- **Detalles de vuelo**: Información completa del itinerario
- **Estado de pago**: Seguimiento de pagos pendientes

## ⚙️ Características Técnicas

### Funcionalidades Avanzadas
- **Sistema de expiración de reservas**: Comando automático para limpiar reservas vencidas
- **Gestión de asientos por vuelo**: Configuración dinámica según el avión asignado
- **Estados de reserva**: Pendiente, Confirmada, Pagada, Cancelada
- **Tipos de asiento**: Económica, Ejecutiva, Primera Clase
- **Manejo de escalas**: Vuelos directos y con conexiones

### Seguridad
- Sistema de autenticación de Django
- Protección CSRF en formularios
- Validación de datos en modelos y formularios
- Separación de permisos por tipo de usuario

## 📁 Archivos Estáticos

```
static/
├── css/
│   └── estilos.css      # Estilos personalizados
└── img/                 # Imágenes del sistema
```

## 🚀 Despliegue

El proyecto incluye configuración para despliegue con:
- `render.yaml` - Configuración para Render.com
- `requirements.txt` - Dependencias Python
- Configuración de archivos estáticos

Para producción, asegúrate de:
1. Configurar variables de entorno para la base de datos
2. Ajustar `ALLOWED_HOSTS` en settings.py
3. Configurar un servidor web (Nginx/Apache)
4. Usar PostgreSQL en lugar de SQLite

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu característica (`git checkout -b feature/NuevaCaracteristica`)
3. Commit tus cambios (`git commit -m 'Agregar nueva característica'`)
4. Push a la rama (`git push origin feature/NuevaCaracteristica`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia [Especificar Licencia].

## 📧 Contacto

Para soporte o consultas sobre el sistema, contacta a [tu-email@ejemplo.com].

---

**Desarrollado con ❤️ usando Django**