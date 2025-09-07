import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import pymysql

# --- Recuperación de contraseña ---
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

# Importa tus modelos
from basedatos.models import db, Usuario

# --- Configuración básica ---
app = Flask(__name__)
app.config['SECRET_KEY'] = "mi_clave_super_secreta_y_unica"  # ✅ clave fija, no cambia en cada reinicio

# Configuración de la base de datos MySQL en Laragon
DB_URL = 'mysql+pymysql://root:@127.0.0.1:3306/Tienda_db'
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}

# --- Configuración del correo ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'nataliamelendez2426@gmail.com'       # ⚡ tu correo
app.config['MAIL_PASSWORD'] = 'tipzwgmlugeudxnu'                   # ⚡ clave de aplicación (sin espacios)
app.config['MAIL_DEFAULT_SENDER'] = ('Soporte Tienda', app.config['MAIL_USERNAME'])

mail = Mail(app)

# Serializador para tokens seguros
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Inicializa la instancia de SQLAlchemy con la aplicación
db.init_app(app)

# Crear base de datos si no existe
with app.app_context():
    engine = create_engine(DB_URL)
    if not database_exists(engine.url):
        create_database(engine.url)
        print("✅ Base de datos 'Tienda_db' creada exitosamente.")
    db.create_all()
    print("✅ Tablas de la base de datos creadas exitosamente.")

# --- RUTAS DE LA APLICACIÓN ---

@app.route('/')
def index():
    return render_template('index.html')

# --- Registro ---
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
                Contraseña=hashed_password,  # ✅ corregido
                Rol='cliente',
                Activo=True
            )

            db.session.add(new_user)
            db.session.commit()

            flash('Cuenta creada exitosamente! Inicia sesión.')
            return redirect(url_for('login'))

        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Ocurrió un error al registrar el usuario: {str(e)}')
            return render_template('register.html')

    return render_template('register.html')

# --- Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Por favor, ingresa tu correo y contraseña.')
            return render_template('login.html')

        user = Usuario.query.filter_by(Correo=email).first()

        if user and check_password_hash(user.Contrasena, password):  # ✅ corregido
            session['user_id'] = user.ID_Usuario
            session['username'] = user.Nombre
            flash('Has iniciado sesión con éxito!')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales inválidas.')
            return redirect(url_for('login'))

    return render_template('login.html')

# --- Dashboard ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# --- Logout ---
@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión.')
    return redirect(url_for('index'))

# --- Nosotros ---
@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')

# --- Recuperación de contraseña ---
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = Usuario.query.filter_by(Correo=email).first()
        if user:
            token = s.dumps(email, salt='password-recovery')
            link = url_for('reset_password', token=token, _external=True)

            msg = Message("Recuperar contraseña", recipients=[email])
            msg.body = f"Para restablecer tu contraseña, haz clic en el siguiente enlace: {link}"
            try:
                mail.send(msg)
                print(f"📧 Correo enviado a {email} con link {link}")  # ✅ debug
            except Exception as e:
                print("❌ Error al enviar correo:", e)
                flash('No se pudo enviar el correo de recuperación.')
                return redirect(url_for('forgot_password'))

            flash('Se envió un enlace de recuperación a tu correo.')
            return redirect(url_for('login'))
        else:
            flash('El correo no está registrado.')
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-recovery', max_age=3600)  # ✅ 1 hora de validez
    except (SignatureExpired, BadSignature):
        flash('El enlace ha expirado o no es válido.')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash('Las contraseñas no coinciden.')
            return render_template('reset_password.html')

        user = Usuario.query.filter_by(Correo=email).first()
        if user:
            user.Contrasena = generate_password_hash(new_password)  # ✅ se guarda encriptada
            db.session.commit()
            flash('Tu contraseña ha sido restablecida con éxito.')
            return redirect(url_for('login'))

    return render_template('reset_password.html')


# --- Prueba de correo ---
@app.route('/test_mail')
def test_mail():
    try:
        msg = Message("Prueba Flask-Mail", recipients=[app.config['MAIL_USERNAME']])
        msg.body = "✅ Si ves este mensaje, tu configuración de correo funciona."
        mail.send(msg)
        return "Correo de prueba enviado correctamente."
    except Exception as e:
        return f"❌ Error al enviar correo: {e}"

# --- Iniciar app ---
if __name__ == '__main__':
    app.run(debug=True)
