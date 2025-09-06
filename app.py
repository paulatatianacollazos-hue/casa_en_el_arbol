import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import pymysql

# Importa el objeto 'db' y los modelos desde tu archivo de modelos
from basedatos.models import db, Usuario

# Configuración de la aplicación
app = Flask(__name__)

# Configuración de la base de datos MySQL en Laragon
DB_URL = 'mysql+pymysql://root:@127.0.0.1:3306/tienda_db'
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'clave_super_secreta'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}

# Inicializa la instancia de SQLAlchemy con la aplicación
db.init_app(app)

# Crea la base de datos y las tablas si no existen
with app.app_context():
    engine = create_engine(DB_URL)
    if not database_exists(engine.url):
        create_database(engine.url)
        print("Base de datos 'casaarbol' creada exitosamente.")
    db.create_all()
    print("Tablas de la base de datos creadas exitosamente.")

# --- RUTAS DE LA APLICACIÓN ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')

        if not name or not email or not password:
            flash('Por favor, completa todos los campos requeridos.')
            return render_template('register.html')

        try:
            existing_user = Usuario.query.filter_by(Correo=email).first()
            if existing_user:
                flash('El correo electrónico ya está registrado. Por favor, usa otro.')
                return render_template('register.html')

            hashed_password = generate_password_hash(password)
            
            new_user = Usuario(
                Nombre=name,
                Correo=email,
                Telefono=phone,
                Contraseña=hashed_password,
                Rol='cliente',
                Activo=True
            )
            
            print(f'Intentando agregar usuario: {new_user.Correo}')
            db.session.add(new_user)
            db.session.commit()

            flash('Cuenta creada exitosamente! Por favor, inicia sesión.')
            return redirect(url_for('login'))
        
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Ocurrió un error al intentar registrar el usuario: {str(e)}')
            return render_template('register.html')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Por favor, ingresa tu correo y contraseña.')
            return render_template('login.html')

        user = Usuario.query.filter_by(Correo=email).first()

        if user and check_password_hash(user.Contraseña, password):
            session['user_id'] = user.ID_Usuario
            session['username'] = user.Nombre
            flash('Has iniciado sesión con éxito!')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales inválidas. Por favor, revisa tu correo y contraseña.')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Has cerrado sesión.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)


