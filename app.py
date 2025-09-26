import os
import re
from datetime import datetime, timedelta

from flask import Flask, render_template
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.exc import SQLAlchemyError
from flask_login import (
    LoginManager, login_required, current_user,
    login_user, logout_user
)

# ------------------ BASE DE DATOS ------------------ #
from basedatos.models import db, Usuario

# ------------------ BLUEPRINTS ------------------ #
from routes.cliente import cliente
from routes.administrador import admin
from routes.auth import auth  # <--- NUEVO para login, registro y logout

# ------------------ CONFIG ------------------ #
app = Flask(__name__)

app.config['SECRET_KEY'] = "mi_clave_super_secreta_y_unica"
DB_URL = 'mysql+pymysql://root:2426@127.0.0.1:3306/Tienda_db'
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}

# Configuración de correo
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'casaenelarbol236@gmail.com'
app.config['MAIL_PASSWORD'] = 'usygdligtlewedju'
app.config['MAIL_DEFAULT_SENDER'] = ('Casa en arbol', app.config['MAIL_USERNAME'])

mail = Mail(app)
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
db.init_app(app)

# ------------------ FLASK-LOGIN ------------------ #
login_manager = LoginManager()
login_manager.login_view = "auth.login"  
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# ------------------ REGISTRO DE BLUEPRINTS ------------------ #
app.register_blueprint(cliente, url_prefix="/cliente")
app.register_blueprint(admin, url_prefix="/admin")
app.register_blueprint(auth, url_prefix="/auth")

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

# ------------------ MAIN ------------------ #
if __name__ == '__main__':
    app.run(debug=True)
