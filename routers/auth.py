import os
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from datetime import datetime
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import re



from flask_login import (
    LoginManager, login_required, current_user,
    login_user, logout_user
)


from functools import wraps

from basedatos.models import db, Usuario, Direccion, Notificaciones, Calendario,Producto,Pedido, Detalle_Pedido
# ------------------ CONFIG ------------------ #
app = Flask(__name__)
instalaciones = []
reviews=[]

app.config['SECRET_KEY'] = "mi_clave_super_secreta_y_unica"

DB_URL = 'mysql+pymysql://root:2426@127.0.0.1:3306/Tienda_db'
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}

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


auth = Blueprint('auth', __name__, url_prefix='/auth')


def validar_password(password):
    if len(password) < 8:
        return "La contraseña debe tener al menos 8 caracteres."
    if not re.search(r"[A-Z]", password):
        return "La contraseña debe contener al menos una letra mayúscula."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "La contraseña debe contener al menos un carácter especial."
    if re.search(r"(012|123|234|345|456|567|678|789)", password):
        return "La contraseña no puede contener números consecutivos."
    return None


def validar_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)


def crear_notificacion(user_id, titulo, mensaje):
    noti = Notificaciones(
        ID_Usuario=user_id,
        Titulo=titulo,
        Mensaje=mensaje
    )
    db.session.add(noti)
    db.session.commit()

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre_completo = request.form.get('name', '').strip()
        correo = request.form.get('email', '').strip()
        telefono = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()

        if not nombre_completo or not correo or not password:
            flash('Nombre, correo y contraseña son obligatorios.', 'warning')
            return render_template('register.html')

        if not validar_email(correo):
            flash('El correo electrónico no tiene un formato válido.', 'danger')
            return render_template('register.html')

        error = validar_password(password)
        if error:
            flash(error, 'register_danger')
            return render_template('register.html')

        partes = nombre_completo.split(" ", 1)
        nombre = partes[0]
        apellido = partes[1] if len(partes) > 1 else ""

        if Usuario.query.filter_by(Correo=correo).first():
            flash('Ya existe una cuenta con ese correo.', 'danger')
            return render_template('register.html')

        try:
            nuevo_usuario = Usuario(
                Nombre=nombre,
                Apellido=apellido,
                Telefono=telefono,
                Correo=correo,
                Contraseña=generate_password_hash(password),
                Rol="cliente"
            )
            db.session.add(nuevo_usuario)
            db.session.commit()

            crear_notificacion(
                user_id=nuevo_usuario.ID_Usuario,
                titulo="¡Bienvenido a Casa en el Árbol!",
                mensaje="Tu cuenta se ha creado correctamente. Explora nuestros productos y promociones."
            )

            flash('Cuenta creada correctamente, ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear la cuenta: {str(e)}', 'danger')
            return render_template('register.html')

    return render_template('register.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('email')
        password = request.form.get('password')

        usuario = Usuario.query.filter_by(Correo=correo).first()
        if usuario and check_password_hash(usuario.Contraseña, password):
            login_user(usuario)
            flash("✅ Inicio de sesión exitoso", "success")

            if usuario.Rol == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
            elif usuario.Rol == 'cliente':
                return redirect(url_for('dashboard'))
            elif usuario.Rol == 'instalador':
                return redirect(url_for('instalador.instalador_dashboard'))
            elif usuario.Rol == 'transportista':
                return redirect(url_for('transportista.transportista_dashboard'))
            else:
                flash("⚠️ Rol desconocido, contacta al administrador.", "warning")
                return redirect(url_for('auth.login'))
        else:
            flash("❌ Correo o contraseña incorrectos", "danger")
            return render_template('login.html')

    return render_template('login.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('auth.login'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get("email")
        user = Usuario.query.filter_by(Correo=email).first()
        if user:
            try:
                token = s.dumps(email, salt='password-recovery')
                send_reset_email(user_email=email, user_name=user.Nombre, token=token)
                flash('📩 Se envió el enlace a tu correo', 'success')
            except Exception as e:
                print(f"Error al enviar correo: {e}")
                flash('❌ No se pudo enviar el correo', 'danger')
        else:
            flash('⚠️ Correo no registrado', 'warning')
    return render_template("forgot_password.html")

@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-recovery', max_age=3600).strip().lower()
    except (SignatureExpired, BadSignature):
        flash('❌ Enlace expirado o inválido', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not new_password or not confirm_password:
            flash('⚠️ Completa ambos campos', 'warning')
            return render_template('reset_password.html', token=token)
        if new_password != confirm_password:
            flash('⚠️ Las contraseñas no coinciden', 'warning')
            return render_template('reset_password.html', token=token)

        user = Usuario.query.filter_by(Correo=email).first()
        if not user:
            flash('❌ Usuario no encontrado', 'danger')
            return redirect(url_for('forgot_password'))

        user.Contraseña = generate_password_hash(new_password)
        db.session.commit()

        crear_notificacion(
            user_id=user.ID_Usuario,
            titulo="Contraseña actualizada 🔑",
            mensaje="Tu contraseña ha sido cambiada exitosamente."
        )

        flash('✅ Contraseña restablecida. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)



