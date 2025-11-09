import os
from flask import Flask, render_template, flash, redirect, url_for
from flask_login import LoginManager
from basedatos.queries import get_productos, get_producto_by_id
from flask_wtf.csrf import CSRFProtect

# ------------------ MODELOS ------------------ #
from basedatos.models import db, Usuario

# ------------------ EXTENSIONES ------------------ #
from basedatos.decoradores import mail

# ------------------ BLUEPRINTS ------------------ #
from routes.auth import auth
from routes.cliente import cliente
from routes.administrador.routes import admin
from routes.empleado.routers import empleado


# ------------------ APP ------------------ #
app = Flask(__name__)
app.register_blueprint(empleado)

csrf = CSRFProtect()
csrf.init_app(app)

# ------------------ CONFIGURACIÓN PRINCIPAL ------------------ #
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "mi_clave_super_secreta_y_unica"),
    SQLALCHEMY_DATABASE_URI=os.getenv(
        "DATABASE_URI",
        "mysql+pymysql://root:paula123@127.0.0.1:3306/Tienda_db"
    ),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},

    # 📂 Carpeta de subida de imágenes
    UPLOAD_FOLDER=os.path.join(os.path.dirname(__file__), "static", "img"),

    # 🔒 Opcional: límite de tamaño de archivos (5 MB en este caso)
    MAX_CONTENT_LENGTH=5 * 1024 * 1024
)

if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

# ------------------ CONFIGURACIÓN MAIL ------------------ #
app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", "casaenelarbol236@gmail.com"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", "usygdligtlewedju"),
    MAIL_DEFAULT_SENDER=(
        "Casa en el Árbol",
        os.getenv("MAIL_USERNAME", "casaenelarbol236@gmail.com"),
    ),
)
mail.init_app(app)

# ------------------ DB ------------------ #
db.init_app(app)

# ------------------ FLASK LOGIN ------------------ #
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = """Debes iniciar sesión para acceder
a esta página."""
login_manager.login_message_category = "warning"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    """Carga un usuario a partir del ID para Flask-Login"""
    try:
        return Usuario.query.get(int(user_id))
    except Exception as e:
        print(f"⚠️ Error cargando usuario: {e}")
        return None


# ------------------ REGISTRO DE BLUEPRINTS ------------------ #
# No redefinimos url_prefix aquí, ya está en cada blueprint
app.register_blueprint(auth)
app.register_blueprint(cliente)
app.register_blueprint(admin)


# ------------------ RUTAS PÚBLICAS ------------------ #
@app.route("/")
def index():
    return render_template("common/index.html")


@app.route("/nosotros")
def nosotros():
    return render_template("common/nosotros.html")


@app.route("/catalogo")
def catalogo():
    productos = get_productos()
    return render_template("common/catalogo.html", productos=productos)


@app.route("/producto/<int:id_producto>")
def detalle_producto(id_producto):
    producto = get_producto_by_id(id_producto)
    if not producto:
        flash("Producto no encontrado", "error")
        return redirect(url_for("admin.catalogo"))
    return render_template("common/detalles.html", producto=producto)


# ------------------ DEBUG: MOSTRAR TODAS LAS RUTAS ------------------ #
with app.app_context():
    print("\n🔗 RUTAS REGISTRADAS:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint:35s} -> {rule}")
    print("-----------------------------\n")


# ------------------ MAIN ------------------ #
if __name__ == "__main__":
    app.run(debug=True)
