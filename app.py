import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from flask_login import (
    LoginManager, login_required, current_user,
    login_user, logout_user
)
from functools import wraps

from basedatos.models import db, Usuario, Direccion, Notificaciones

app = Flask(__name__)
app.config['SECRET_KEY'] = "mi_clave_super_secreta_y_unica"

DB_URL = 'mysql+pymysql://root:@127.0.0.1:3306/Tienda_db'
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

# ------------------ FLASK-LOGIN ------------------ #
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# ------------------ DECORADOR DE ROLES ------------------ #
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("⚠️ Debes iniciar sesión para acceder.", "warning")
                return redirect(url_for("login"))
            if current_user.Rol.lower() not in [r.lower() for r in roles]:
                flash("❌ No tienes permisos para acceder a esta página.", "danger")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return wrapped
    return decorator

# ------------------ FUNCIONES ------------------ #
def crear_notificacion(user_id, titulo, mensaje):
    """Crea y guarda una notificación real para un usuario"""
    noti = Notificaciones(
        ID_Usuario=user_id,
        Titulo=titulo,
        Mensaje=mensaje
    )
    db.session.add(noti)
    db.session.commit()

# ------------------ RUTAS ------------------ #
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre_completo = request.form.get('name', '').strip()
        correo = request.form.get('email', '').strip()
        telefono = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()

        if not nombre_completo or not correo or not password:
            flash('Nombre, correo y contraseña son obligatorios.', 'warning')
            return render_template('register.html')

        partes = nombre_completo.split(" ", 1)
        nombre = partes[0]
        apellido = partes[1] if len(partes) > 1 else ""

        if Usuario.query.filter_by(Correo=correo).first():
            flash('Ya existe una cuenta con ese correo.', 'danger')
            return render_template('register.html')

        nuevo_usuario = Usuario(
            Nombre=nombre,
            Apellido=apellido,
            Telefono=telefono,
            Correo=correo,
            Contraseña=generate_password_hash(password)
        )
        db.session.add(nuevo_usuario)
        db.session.commit()

        crear_notificacion(
            user_id=nuevo_usuario.ID_Usuario,
            titulo="¡Bienvenido a Casa en el Árbol!",
            mensaje="Tu cuenta se ha creado correctamente. Explora nuestros productos y promociones."
        )

        flash('Cuenta creada correctamente, ahora puedes completar tu información en el perfil.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Usamos .get() para evitar KeyError si el input no existe
        correo = request.form.get('correo')  
        password = request.form.get('password')

        if not correo or not password:
            flash("⚠️ Debes completar todos los campos", "warning")
            return redirect(url_for('login'))

        usuario = Usuario.query.filter_by(Correo=correo).first()

        if usuario and check_password_hash(usuario.Contraseña, password):
            login_user(usuario)
            flash("✅ Inicio de sesión exitoso", "success")

            # Redirigir según el rol
            if usuario.Rol == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif usuario.Rol == 'cliente':
                return redirect(url_for('dashboard'))
            elif usuario.Rol == 'instalador':
                return redirect(url_for('instalador_dashboard'))
            elif usuario.Rol == 'transportista':
                return redirect(url_for('transportista_dashboard'))
            else:
                flash("⚠️ Rol desconocido, contacta al administrador.", "warning")
                return redirect(url_for('login'))
        else:
            flash("❌ Correo o contraseña incorrectos", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()   # ✅ cerrar sesión con Flask-Login
    session.clear()
    flash("Sesión cerrada correctamente", "info")
    return redirect(url_for('index'))

@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get("email")
        # Aquí iría la lógica de recuperación (enviar mail, etc.)
        flash("📧 Si tu correo está registrado, recibirás instrucciones.", "info")
        return redirect(url_for("login"))

    return render_template("forgot_password.html")

# ------------------ GESTIÓN DE ROLES ------------------ #
@app.route('/gestion_roles', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def gestion_roles():
    if request.method == 'POST':
        user_id = request.form.get('user_id')  
        nuevo_rol = request.form.get('rol')    

        if not user_id or not nuevo_rol:
            flash("⚠️ Selecciona un usuario y un rol válido", "warning")
            return redirect(url_for('gestion_roles'))

        usuario = Usuario.query.get(user_id)
        if not usuario:
            flash("❌ Usuario no encontrado", "danger")
            return redirect(url_for('gestion_roles'))

        usuario.Rol = nuevo_rol
        db.session.commit()

        flash(f"✅ Rol de {usuario.Nombre} actualizado a {nuevo_rol}", "success")
        return redirect(url_for('gestion_roles'))

    usuarios = Usuario.query.all()
    roles_disponibles = ["admin", "cliente", "instalador", "transportista"]

    return render_template("gestion_roles.html", usuarios=usuarios, roles=roles_disponibles)

# ------------------ DASHBOARDS ------------------ #
@app.route('/admin_dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    return render_template('administrador/admin_dashboard.html')

@app.route('/dashboard')
@login_required
@role_required('cliente')
def dashboard():
    return render_template('dashboard.html')

@app.route('/instalador_dashboard')
@login_required
@role_required('instalador')
def instalador_dashboard():
    return render_template('instalador_dashboard.html')

@app.route('/transportista_dashboard')
@login_required
@role_required('transportista')
def transportista_dashboard():
    return render_template('transportista_dashboard.html')

# ------------------ MAIN ------------------ #
if __name__ == '__main__':
    app.run(debug=True)
