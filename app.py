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
from routes.administrador import admin  # Asegúrate que dentro de este Blueprint esté url_prefix='/admin'

# ------------------ APP ------------------ #
app = Flask(__name__)
app.config['SECRET_KEY'] = "mi_clave_super_secreta_y_unica"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:2426@127.0.0.1:3306/Tienda_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}

# ------------------ MAIL ------------------ #
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'casaenelarbol236@gmail.com'
app.config['MAIL_PASSWORD'] = 'usygdligtlewedju'
app.config['MAIL_DEFAULT_SENDER'] = ('Casa en el Árbol', app.config['MAIL_USERNAME'])
mail.init_app(app)  

# ------------------ DB ------------------ #
db.init_app(app)

# ------------------ FLASK LOGIN ------------------ #
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# ------------------ REGISTRO DE BLUEPRINTS ------------------ #
app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(cliente, url_prefix='/cliente')
app.register_blueprint(admin)  # ✅ NO repetimos url_prefix aquí, ya debe estar en el Blueprint

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
print("🔗 Rutas registradas:")
with app.app_context():
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint:30s} -> {rule}")

# ------------------ MAIN ------------------ #
if __name__ == '__main__':
    app.run(debug=True)
