import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, Float, Text, Time, ForeignKey
from sqlalchemy.orm import relationship


# Asumiendo que tus modelos están en 'models.py'
# y que en ese archivo tienes algo como:
# from flask_sqlalchemy import SQLAlchemy
# db = SQLAlchemy()
# class Usuario(db.Model):
#    ...
#    ID_Usuario = db.Column(db.Integer, primary_key=True)
#    ...
# Por favor, asegúrate de que el objeto 'db' en models.py
# esté vinculado a la aplicación de Flask antes de su uso.

# CORREGIDO: Usar una importación absoluta en lugar de una relativa.
# Si tu archivo models.py está en la misma carpeta que app.py, usa:
# from models import db, Usuario
# Si está en una subcarpeta, por ejemplo 'database', usa:
# from database.models import db, Usuario
from basedatos.models import db, Usuario

# Configuración de la aplicación
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1:3306/Tienda_Casa_en_el_arbol'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'clave_secreta'

# Vincula la instancia de SQLAlchemy a la aplicación
db.init_app(app)

# Para que el `db.create_all()` funcione correctamente
# con los modelos en un archivo separado, debes importarlos
# después de que la aplicación sea creada.
# from .models import Usuario # Ya está importado arriba
# with app.app_context():
#    db.create_all()


# --- RUTAS DE LA APLICACIÓN ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Por favor, ingresa tu correo y contraseña.')
            return render_template('login.html')

        try:
            # CORREGIDO: ahora usamos `db.session` y `Usuario.query` ya que el modelo está
            # ligado al objeto `db` de la aplicación.
            user = db.session.query(Usuario).filter_by(Correo=email).first()

            if user and user.Contraseña == password:
                session['user_id'] = user.ID_Usuario
                session['username'] = user.Nombre
                
                flash('Has iniciado sesión con éxito!')
                return redirect(url_for('dashboard'))
            else:
                flash('Credenciales inválidas. Por favor, revisa tu correo y contraseña.')
                return redirect(url_for('login'))

        except SQLAlchemyError as e:
            flash(f'Ocurrió un error al intentar iniciar sesión: {str(e)}')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')

        if not name or not email or not password:
            flash('Por favor, completa todos los campos requeridos.')
            return render_template('registro.html')

        try:
            # CORREGIDO: Uso de `db.session.query` para consultar la base de datos
            existing_user = db.session.query(Usuario).filter_by(Correo=email).first()
            if existing_user:
                flash('El correo electrónico ya está registrado. Por favor, usa otro.')
                return render_template('registro.html')

            new_user = Usuario(Nombre=name, Correo=email, Telefono=phone, Contraseña=password)

            db.session.add(new_user)
            db.session.commit()

            flash('Cuenta creada exitosamente! Por favor, inicia sesión.')
            return redirect(url_for('login'))

        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Ocurrió un error al intentar registrar el usuario: {str(e)}')
            return render_template('registro.html')

    return render_template('registro.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)
