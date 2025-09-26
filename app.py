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
from routes.administrador import admin  # ✅ Asegúrate que el Blueprint se llame admin y tenga url_prefix='/admin'

# ------------------ APP ------------------ #
app = Flask(__name__)

# Configuración principal
app.config.update(
    SECRET_KEY="mi_clave_super_secreta_y_unica",
    SQLALCHEMY_DATABASE_URI="mysql+pymysql://root:2426@127.0.0.1:3306/Tienda_db",
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={'pool_pre_ping': True},
)

# ------------------ MAIL ------------------ #
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME='casaenelarbol236@gmail.com',
    MAIL_PASSWORD='usygdligtlewedju',
    MAIL_DEFAULT_SENDER=('Casa en el Árbol', 'casaenelarbol236@gmail.com'),
)
mail.init_app(app)

# ------------------ DB ------------------ #
db.init_app(app)

# ------------------ FLASK LOGIN ------------------ #
login_manager = LoginManager()
login_manager.login_view = "auth.login"  # Endpoint de login (auth es el nombre del blueprint)
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# ------------------ REGISTRO DE BLUEPRINTS ------------------ #
# ✅ IMPORTANTE: url_prefix SOLO se define en el blueprint, no aquí
app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(cliente, url_prefix='/cliente')
app.register_blueprint(admin)  # admin ya tiene url_prefix='/admin' en su definición

# ------------------ RUTAS PÚBLICAS ------------------ #
@app.route('/')
def index():
    return render_template('common/index.html')

@app.route('/nosotros')
def nosotros():
    return render_template('common/nosotros.html')

@app.route('/catalogo')
def catalogo():
    return render_template('common/catalogo.html')

# ------------------ DEBUG: MOSTRAR TODAS LAS RUTAS ------------------ #
with app.app_context():
    print("\n🔗 RUTAS REGISTRADAS:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint:30s} -> {rule}")
    print("-----------------------------\n")

# ------------------ MAIN ------------------ #
if __name__ == '__main__':
    app.run(debug=True)
