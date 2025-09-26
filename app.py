import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# ------------------ MODELOS ------------------ #
from basedatos.models import db, Usuario

# ------------------ EXTENSIONES ------------------ #
from basedatos.decoradores import mail

# ------------------ BLUEPRINTS ------------------ #
from routes.auth import auth
from routes.cliente import cliente
from routes.administrador import admin  # ✅ Blueprint admin con url_prefix='/admin'

# ------------------ APP ------------------ #
app = Flask(__name__)

# ------------------ CONFIGURACIÓN PRINCIPAL ------------------ #
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "mi_clave_super_secreta_y_unica"),
    SQLALCHEMY_DATABASE_URI=os.getenv(
        "DATABASE_URI", "mysql+pymysql://root:2426@127.0.0.1:3306/Tienda_db"
    ),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
)

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
login_manager.login_message = "Debes iniciar sesión para acceder a esta página."
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
    return render_template("common/catalogo.html")


# ------------------ DEBUG: MOSTRAR TODAS LAS RUTAS ------------------ #
with app.app_context():
    print("\n🔗 RUTAS REGISTRADAS:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint:35s} -> {rule}")
    print("-----------------------------\n")


# ------------------ MAIN ------------------ #
if __name__ == "__main__":
    app.run(debug=True)
