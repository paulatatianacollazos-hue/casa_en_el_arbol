import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from basedatos.models import db, Usuario

app = Flask(__name__)
app.config['SECRET_KEY'] = "mi_clave_super_secreta_y_unica"

# --- Configuración de la base de datos MySQL ---
DB_URL = 'mysql+pymysql://root:@127.0.0.1:3306/Tienda_db'
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}

# --- Configuración de correo ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'nataliamelendez2426@gmail.com'
app.config['MAIL_PASSWORD'] = 'tipzwgmlugeudxnu'
app.config['MAIL_DEFAULT_SENDER'] = ('Soporte Tienda', app.config['MAIL_USERNAME'])

mail = Mail(app)
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Inicializa SQLAlchemy
db.init_app(app)

# Crear base de datos si no existe
with app.app_context():
    engine = create_engine(DB_URL)
    if not database_exists(engine.url):
        create_database(engine.url)
        print("✅ Base de datos creada")
    db.create_all()
    print("✅ Tablas creadas")

# --- Rutas ---
@app.route('/')
def index():
    return render_template('index.html')

# Registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')

        if not name or not email or not password:
            flash('Completa todos los campos')
            return render_template('register.html')

        try:
            if Usuario.query.filter_by(Correo=email).first():
                flash('Correo ya registrado')
                return render_template('register.html')

            hashed_password = generate_password_hash(password)
            user = Usuario(Nombre=name, Correo=email, Telefono=phone, Contraseña=hashed_password, Rol='cliente', Activo=True)
            db.session.add(user)
            db.session.commit()

            flash('Cuenta creada. ¡Ahora inicia sesión!')
            return redirect(url_for('login'))

        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Error al registrar: {str(e)}')
            return render_template('register.html')

    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Ingresa correo y contraseña')
            return render_template('login.html')

        user = Usuario.query.filter_by(Correo=email).first()
        if user and check_password_hash(user.Contraseña, password):
            session['user_id'] = user.ID_Usuario
            session['username'] = user.Nombre
            flash('Inicio de sesión exitoso')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales inválidas')
            return render_template('login.html')

    return render_template('login.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión')
    return redirect(url_for('index'))

# Nosotros (sin cambios)
@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')

# Recuperación de contraseña
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = Usuario.query.filter_by(Correo=email).first()
        if user:
            token = s.dumps(email, salt='password-recovery')
            link = url_for('reset_password', token=token, _external=True)
            msg = Message("Recuperar contraseña", recipients=[email])
            msg.body = f"Para restablecer tu contraseña, haz clic: {link}"
            try:
                mail.send(msg)
                flash('Se envió el enlace a tu correo')
            except Exception as e:
                flash('No se pudo enviar el correo')
                print(e)
        else:
            flash('Correo no registrado')
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-recovery', max_age=3600)
        email = email.strip().lower()  # Normaliza el correo
    except (SignatureExpired, BadSignature):
        flash('Enlace expirado o inválido')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not new_password or not confirm_password:
            flash('Completa ambos campos')
            return render_template('reset_password.html')
        if new_password != confirm_password:
            flash('Contraseñas no coinciden')
            return render_template('reset_password.html')

        try:
            user = Usuario.query.filter_by(Correo=email).first()
            if not user:
                flash('Usuario no encontrado')
                return redirect(url_for('forgot_password'))

            # 🔑 Guarda la nueva contraseña con hash
            user.Contraseña = generate_password_hash(new_password)

            db.session.commit()  # 🚀 Aplica cambios
            flash('Contraseña restablecida correctamente. Inicia sesión con la nueva')

            # Limpia la sesión
            session.pop('user_id', None)
            session.pop('username', None)

            return redirect(url_for('login'))

        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Error al actualizar la contraseña: {str(e)}')
            return render_template('reset_password.html')

    return render_template('reset_password.html')



# Prueba de correo
@app.route('/test_mail')
def test_mail():
    try:
        msg = Message("Prueba", recipients=[app.config['MAIL_USERNAME']])
        msg.body = "✅ Configuración de correo funciona"
        mail.send(msg)
        return "Correo enviado correctamente"
    except Exception as e:
        return f"Error: {e}"


if __name__ == '__main__':
    app.run(debug=True)
