import os
import uuid
import pymysql
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from werkzeug.security import generate_password_hash, check_password_hash

# Chatbot y modelos
from basedatos.models import db, Usuario
from chatbot.knowledge_base import ChatbotKnowledge
from chatbot.response_handler import ResponseHandler
from chatbot.session_manager import SessionManager

from flask_socketio import SocketIO, emit  # Asegúrate de haber instalado flask-socketio

# Inicializar app
app = Flask(__name__)
socketio = SocketIO(app)

# Configuración de base de datos
DB_URL = 'mysql+pymysql://root:@127.0.0.1:3306/tienda_db'
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'clave_super_secreta'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}

# Inicializar base de datos
db.init_app(app)

with app.app_context():
    engine = create_engine(DB_URL)
    if not database_exists(engine.url):
        create_database(engine.url)
        print("Base de datos 'tienda_db' creada exitosamente.")
    db.create_all()
    print("Tablas creadas exitosamente.")
    
# --- RUTAS FLASK ---
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
                flash('El correo electrónico ya está registrado.')
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
            db.session.add(new_user)
            db.session.commit()

            flash('Cuenta creada exitosamente. Inicia sesión.')
            return redirect(url_for('login'))

        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Error al registrar: {str(e)}')
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
            flash('Has iniciado sesión con éxito.')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales inválidas.')
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

@app.route('/nosotros')
def nosotros():
    return render_template('Nosotros.html')

