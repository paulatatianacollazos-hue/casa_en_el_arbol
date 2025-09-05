import os
import pymysql
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from werkzeug.security import generate_password_hash, check_password_hash

# Importar modelos
from models import db, Usuario

# Inicializar app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave_super_secreta'

# Configuración de la base de datos
DB_URL = 'mysql+pymysql://root:@127.0.0.1:3306/tienda_db'
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}

# Inicializar DB
db.init_app(app)

with app.app_context():
    engine = create_engine(DB_URL)
    if not database_exists(engine.url):
        create_database(engine.url)
        print("✅ Base de datos 'tienda_db' creada exitosamente.")
    db.create_all()
    print("✅ Tablas creadas exitosamente.")

# --- RUTAS ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')

        if not name or not email or not password:
            flash("⚠️ Todos los campos obligatorios")
            return redirect(url_for('register'))

        usuario_existente = Usuario.query.filter_by(Correo=email).first()
        if usuario_existente:
            flash("❌ El correo ya está registrado")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        nuevo_usuario = Usuario(
            Nombre=name,
            Correo=email,
            Telefono=phone,
            Contraseña=hashed_password,
            Rol="cliente",
            Activo=True
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        flash("✅ Usuario registrado correctamente")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        usuario = Usuario.query.filter_by(Correo=email).first()
        if usuario and check_password_hash(usuario.Contraseña, password):
            session['user_id'] = usuario.ID_Usuario
            session['username'] = usuario.Nombre
            flash("✅ Bienvenido " + usuario.Nombre)
            return redirect(url_for('dashboard'))
        else:
            flash("❌ Credenciales incorrectas")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("👋 Sesión cerrada")
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
