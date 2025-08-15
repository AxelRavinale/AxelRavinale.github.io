# Sistema de Gestión de Aerolínea ✈️

Un sistema web completo desarrollado en Django para la gestión integral de una aerolínea, incluyendo reservas, vuelos, pasajeros, empleados y flota de aviones.

## 🚀 Características Principales

### Para Pasajeros
- **Búsqueda de vuelos** disponibles por fecha y destino
- **Selección de asientos** interactiva con mapa visual del avión
- **Gestión de reservas**: crear, consultar y administrar reservas
- **Sistema de pagos** con fechas límite y estados de pago
- **Consulta pública de boletos** mediante código de reserva
- **Panel personal** para ver historial de reservas

### Para Administradores
- **Gestión de vuelos**: crear, modificar y programar vuelos
- **Administración de escalas** para vuelos con paradas intermedias
- **Gestión de tripulación**: asignar pilotos y personal de cabina
- **Control de flota**: registro y mantenimiento de aviones
- **Gestión de empleados**: alta, baja y modificación de personal
- **Administración de pasajeros**: registro y actualización de datos
- **Configuración de asientos** por tipo de avión
- **Sistema de reservas administrativas** para agencias

## 🏗️ Arquitectura del Sistema

El proyecto está organizado en aplicaciones modulares de Django:

- **autentificacion/ # Sistema de login y registro**
- **aviones/ # Gestión de flota y asientos**
- **core/ # Modelos base y configuración**
- **empleados/ # Administración de personal**
- **flota/ # Gestión de aviones**
- **home/ # Página principal**
- **pasajeros/ # Gestión de pasajeros**
- **reservas/ # Sistema de reservas y boletos**
- **vuelos/ # Programación y gestión de vuelos**

## Además cuenta con:
- `static/` y `staticfiles/` para CSS, JS e imágenes
- `index.html` como página principal
- `manage.py` para administración del proyecto
- `requirements.txt` con dependencias

## 📋 Requisitos del Sistema

- Python 3.10+
- Django 4.x
- SQLite (incluido) o PostgreSQL para producción
- Dependencias listadas en `requirements.txt`

## 🛠️ Instalación

1. **Clonar el repositorio**
```bash
git clone git@github.com:AxelRavinale/AxelRavinale.github.io.git
cd AxelRavinale.github.io

python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate

python manage.py createsuperuser

python manage.py runserver
```

`Accede a la aplicación en http://127.0.0.1:8000 y al panel de administración en http://127.0.0.1:8000/admin.`

### 🗄️ Modelos de Datos Principales
Estructura de Vuelos

Vuelo: Información básica (número, origen, destino, fechas)

Escala: Paradas intermedias con tiempos de conexión

TripulacionVuelo: Asignación de personal (pilotos, azafatas)

Sistema de Reservas

Reserva: Reserva principal con estado de pago

ReservaDetalle: Detalles específicos por pasajero

Boleto: Boleto individual vinculado a asiento

AsientoVuelo: Configuración de asientos por vuelo

Gestión de Personal

Empleado: Datos del personal de la aerolínea

Pasajero: Información de pasajeros registrados

Persona: Modelo base con datos personales

Flota

Avion: Información de la aeronave

Asiento: Configuración de asientos por avión (clase, ubicación)

### 🌐 Internacionalización

Español (es) - Idioma principal

Inglés (en) - Idioma secundario

Archivos de traducción en el directorio locale/.

### 📱 Interfaces de Usuario
Panel de Administración

Completo de Django

Gestión de todos los modelos

Reportes y estadísticas

Interfaz Pública

Búsqueda de vuelos con filtros intuitivos

Selección de asientos interactiva

Proceso de reserva paso a paso

Consulta de boletos por código de reserva

Panel de Usuario

Historial completo de reservas

Detalles de vuelos

Estado de pago

### ⚙️ Características Técnicas

Sistema de expiración de reservas automático

Gestión dinámica de asientos según avión

Estados de reserva: Pendiente, Confirmada, Pagada, Cancelada

Tipos de asiento: Económica, Ejecutiva, Primera Clase

Manejo de vuelos directos y con escalas

Autenticación y permisos de usuario

Protección CSRF y validación de datos

Desarrollado con ❤️ usando Django**