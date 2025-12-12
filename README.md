# Backend del Proyecto

Este backend está desarrollado con Python, Flask, SQLAlchemy y un sistema modular mediante Blueprints. Proporciona toda la lógica necesaria para la gestión de usuarios, roles, pedidos, entregas, notificaciones, catálogos y paneles independientes para administrador, cliente y empleado.

---

## Características Principales

* *Autenticación y cuentas*: Inicio de sesión, registro, recuperación de contraseña, restablecimiento.
* *Roles y permisos*: Administrador, cliente, empleado (instalador / transportista).
* *Paneles independientes*:Dashboard del administrador, Dashboard del cliente y Dashboard del empleado.
* *Gestión de pedidos*: Creación, detalle, seguimiento, historial.
* *Catálogo y productos*: Filtros, detalles, comparación, favoritos.
* *Calendario*: Citas, entregas y eventos de empleados.
* *Subida de archivos*: Gestión de entregas mediante uploads.
* *Secciones informativas: Nosotros, reseñas, dibujitos, formularios, chatbot.
* *Sistema modular*: Blueprints para mantener un backend escalable y organizado.

---

## Estructura del Proyecto

backend/
│   .env.example           # Variables de entorno de ejemplo
│   app.py                 # Punto de entrada del servidor Flask
│   auto_git.sh            # Script opcional de automatización Git
│   requirements.txt       # Dependencias del proyecto
│
├── basedatos/             # Base de datos y configuraciones
│   ├── db.py              # coneccion con la base de datos
│   ├── models.py
│   ├── queries.py
│   └── decoradores.py
│
├── routes/                # Blueprints separados por rol
│   ├── administrador/
│   │   ├── routes.py
│   │   └── __init__.py
│   ├── auth/
│   │   ├── routes.py
│   │   └── __init__.py
│   ├── cliente/
│   │   ├── routes.py
│   │   └── __init__.py
│   └── empleado/
│       ├── routers.py
│       ├── dashboard.py
│       └── __init__.py
│
├── static/                # Archivos estáticos
│   ├── css/
│   │   ├── calendario.css
│   │   ├── control_pedidos.css
│   │   ├── dashboard.css
│   │   ├── formularios.css
│   │   ├── index.css
│   │   ├── index2.css
│   │   ├── nosotros.css
│   │   ├── perfil.css
│   │   ├── reseñas.css
│   │   ├── roles.css
│   │   └── style.css
│   ├── js/
│   │   ├── actualizacion.js
│   │   ├── calendario.js
│   │   ├── calendario_admin.js
│   │   ├── cart.js
│   │   ├── chatbot.js
│   │   ├── estadisticas.js
│   │   ├── formularios.js
│   │   └── main.js
│   ├── img/
│   └── uploads/
│       └── entregas/      # Archivos subidos por empleados
│
└── templates/             # Plantillas HTML
    ├── administrador/
    │   ├── admin_actualizacion_datos.html
    │   ├── admin_dashboard.html
    │   ├── admin_detalle.html
    │   ├── admin_reseñas.html
    │   ├── buscar_admin.html
    │   ├── catalogo.html
    │   ├── control_pedidos.html
    │   ├── estadisticas_reseñas.html
    │   ├── gestion_roles.html
    │   └── notificaciones_admin.html
    │
    ├── cliente/
    │   ├── Actualizacion_datos.html
    │   ├── Nosotros.html
    │   ├── buscar_cliente.html
    │   ├── calendar.html
    │   ├── carrito.html
    │   ├── catalogo_filtros.html
    │   ├── chatbot.html
    │   ├── cliente_catalogo.html
    │   ├── cliente_detalle.html
    │   ├── comparar.html
    │   ├── confirmacion.html
    │   ├── confirmacion_firma.html
    │   ├── dashboard.html
    │   ├── detalle_pedido.html
    │   ├── error.html
    │   ├── escribir.html
    │   ├── favoritos.html
    │   ├── historial_transacciones.html
    │   ├── instalaciones.html
    │   ├── lista.html
    │   ├── mis_pedidos.html
    │   ├── notificaciones_cliente.html
    │   ├── pagos.html
    │   ├── pedido_productos.html
    │   ├── reseñas.html
    │   ├── resultados.html
    │   └── seguimiento.html
    │
    ├── empleado/
    │   ├── Actualizacion_datos.html
    │   ├── Nosotros.html
    │   ├── dashboard.html
    │   ├── registro_entrega.html
    │   ├── email_reset.html
    │   ├── forgot_password.html
    │   ├── login.html
    │   ├── register.html
    │   └── reset_password.html
    │
    └── common/
        ├── partials/
        │   ├── chat_flotante.html
        │   ├── chatbot.html
        │   ├── modals.html
        │   └── Nosotros.html
        ├── base.html
        ├── catalogo.html
        ├── detalles.html
        ├── dibujitos.html
        ├── dibujitos2.html
        ├── dibujitos3.html
        └── index.html

---

## Instalación y Uso

1.Clonar el repositorio:

git clone <url-del-repo>
cd backend

2.Crear entorno virtual:

python -m venv venv
venv\Scripts\activate   # Windows

3.Instalar dependencias:

pip install -r requirements.txt

4.Crear archivo .env basado en .env.example:

FLASK_SECRET_KEY=tu-clave-secreta
DATABASE_URI=mysql+pymysql://user:password@host/basedatos
EMAIL_USER=tu-email@example.com
EMAIL_PASS=contraseña-app
UPLOAD_FOLDER=./static/uploads/entregas

5.Iniciar la aplicación:

python app.py

El backend estará disponible en:

http://localhost:5000

---

## Endpoints Principales

* Auth /auth → Login, registro y restablecer contraseña
* Administrador /admin → Dashboard, gestión de roles, control de pedidos y estadísticas
* Cliente /cliente → Catálogo, carrito, pedidos, favoritos y seguimiento
* Empleado /empleado → Dashboard de entregas, subida de evidencias y gestión de calendario

---

## Tecnologías Utilizadas

* *Node.js* + *Express* → Servidor web
* *Mysql workbench* → Base de datos
* *Flask*
* *Flask-Login*
* *SQLAlchemy*
* *Jinja2*
* *Python-dotenv*
* *Flask-Mail* → Verificacion de correo y cambio de contraseña
* *Bootstrap + JS*

---

## ENV

Variables necesarias:

FLASK_SECRET_KEY="your-secret-key"

DATABASE_URI="your-db-connection-url"

EMAIL_USER="your-email@example.com"
EMAIL_PASS="your-email-app-password"

UPLOAD_FOLDER="./static/uploads/entregas"


