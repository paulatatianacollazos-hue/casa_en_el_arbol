import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
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

# ------------------ CONFIG ------------------ #
app = Flask(__name__)
instalaciones = []

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
    noti = Notificaciones(
        ID_Usuario=user_id,
        Titulo=titulo,
        Mensaje=mensaje
    )
    db.session.add(noti)
    db.session.commit()

def send_reset_email(user_email, user_name, token):
    reset_url = url_for('reset_password', token=token, _external=True)
    msg = Message(
        subject="Restablece tu contraseña - Casa en Arbol",
        recipients=[user_email],
        html=render_template('email_reset.html', user_name=user_name, reset_url=reset_url)
    )
    mail.send(msg)

# ------------------ RUTAS ------------------ #
@app.route('/')
def index():
    return render_template('index.html')

# ---------- Registro ----------
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
        return redirect(url_for('login'))

    return render_template('register.html')

# ---------- Login ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('correo')
        password = request.form.get('password')

        usuario = Usuario.query.filter_by(Correo=correo).first()
        if usuario and check_password_hash(usuario.Contraseña, password):
            login_user(usuario)
            flash("✅ Inicio de sesión exitoso", "success")

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
            return render_template('login.html')

    return render_template('login.html')


# ---------- Página Nosotros ----------
@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')


# ---------- Logout ----------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada correctamente", "info")
    return redirect(url_for('index'))

# ---------- Recuperación contraseña ----------
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

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
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



# ---------- Actualización de datos ----------
@app.route('/actualizacion_datos', methods=['GET', 'POST'])
@login_required
@role_required('cliente', 'instalador', 'transportista', 'admin')
def actualizacion_datos():
    usuario = current_user
    direcciones = Direccion.query.filter_by(ID_Usuario=usuario.ID_Usuario).all()
    notificaciones = Notificaciones.query.filter_by(ID_Usuario=usuario.ID_Usuario).order_by(Notificaciones.Fecha.desc()).all()

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        genero = request.form.get('genero', '').strip()
        correo = request.form.get('correo', '').strip()
        telefono = request.form.get('telefono', '').strip()
        password = request.form.get('password', '').strip()

        if not nombre or not apellido or not correo:
            flash('⚠️ Los campos Nombre, Apellido y Correo son obligatorios.', 'warning')
            return render_template('Actualizacion_datos.html', usuario=usuario, direcciones=direcciones, notificaciones=notificaciones)

        usuario_existente = Usuario.query.filter(
            Usuario.Correo == correo,
            Usuario.ID_Usuario != usuario.ID_Usuario
        ).first()
        if usuario_existente:
            flash('El correo ya está registrado por otro usuario.', 'danger')
            return render_template('Actualizacion_datos.html', usuario=usuario, direcciones=direcciones, notificaciones=notificaciones)

        usuario.Nombre = nombre
        usuario.Apellido = apellido
        usuario.Genero = genero
        usuario.Correo = correo
        usuario.Telefono = telefono
        if password:
            usuario.Contraseña = generate_password_hash(password)

        db.session.commit()

        crear_notificacion(
            user_id=usuario.ID_Usuario,
            titulo="Perfil actualizado ✏️",
            mensaje="Tus datos personales se han actualizado correctamente."
        )

        flash('✅ Perfil actualizado correctamente', 'success')

    return render_template('Actualizacion_datos.html',
                           usuario=usuario,
                           direcciones=direcciones,
                           notificaciones=notificaciones)

# ---------- Direcciones ----------
@app.route('/agregar_direccion', methods=['POST'])
@login_required
def agregar_direccion():
    nueva_direccion = Direccion(
        ID_Usuario=current_user.ID_Usuario,
        Pais="Colombia",
        Departamento="Bogotá, D.C.",
        Ciudad="Bogotá",
        Direccion=request.form.get('direccion'),
        InfoAdicional=request.form.get('infoAdicional'),
        Barrio=request.form.get('barrio'),
        Destinatario=request.form.get('destinatario')
    )
    db.session.add(nueva_direccion)
    db.session.commit()

    crear_notificacion(
        user_id=current_user.ID_Usuario,
        titulo="Dirección agregada 🏠",
        mensaje=f"Se ha agregado una nueva dirección: {nueva_direccion.Direccion}"
    )

    return redirect(url_for('actualizacion_datos'))

@app.route('/borrar_direccion/<int:id_direccion>', methods=['POST'])
@login_required
def borrar_direccion(id_direccion):
    direccion = Direccion.query.get_or_404(id_direccion)
    db.session.delete(direccion)
    db.session.commit()

    crear_notificacion(
        user_id=current_user.ID_Usuario,
        titulo="Dirección eliminada 🗑️",
        mensaje=f"La dirección '{direccion.Direccion}' ha sido eliminada."
    )

    flash("Dirección eliminada correctamente 🗑️", "success")
    return redirect(url_for('actualizacion_datos'))

# ---------- Notificaciones ----------
# ---------------------------
# 📌 NOTIFICACIONES CLIENTE
# ---------------------------
@app.route('/notificaciones', methods=['GET', 'POST'])
@login_required
def ver_notificaciones_cliente():
    if request.method == 'POST':
        ids = request.form.getlist('ids')
        if ids:
            Notificaciones.query.filter(
                Notificaciones.ID_Usuario == current_user.ID_Usuario,
                Notificaciones.ID_Notificacion.in_(ids)
            ).delete(synchronize_session=False)
            db.session.commit()
            flash("✅ Notificaciones eliminadas", "success")
        return redirect(url_for('ver_notificaciones_cliente'))

    notificaciones = Notificaciones.query.filter_by(
        ID_Usuario=current_user.ID_Usuario
    ).order_by(Notificaciones.Fecha.desc()).all()
    
    return render_template("notificaciones_cliente.html", notificaciones=notificaciones)




# ---------------------------
# 📌 NOTIFICACIONES ADMIN
# ---------------------------
@app.route('/notificaciones_admin', methods=['GET', 'POST'])
@login_required
@role_required('admin')  # obligatorio si solo admins deben ver esto
def ver_notificaciones_admin():
    if request.method == 'POST':
        ids = request.form.getlist('ids')
        if not ids:
            flash("❌ No seleccionaste ninguna notificación", "warning")
            return redirect(url_for('ver_notificaciones_admin'))

        try:
            ids_int = [int(i) for i in ids if str(i).isdigit()]
        except ValueError:
            flash("❌ IDs inválidos", "danger")
            return redirect(url_for('ver_notificaciones_admin'))

        try:
            Notificaciones.query.filter(
                Notificaciones.ID_Usuario == current_user.ID_Usuario,
                Notificaciones.ID_Notificacion.in_(ids_int)
            ).delete(synchronize_session=False)
            db.session.commit()
            flash("✅ Notificaciones eliminadas", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error al eliminar: {e}", "danger")

        return redirect(url_for('ver_notificaciones_admin'))

    notificaciones = Notificaciones.query.filter_by(
        ID_Usuario=current_user.ID_Usuario
    ).order_by(Notificaciones.Fecha.desc()).all()
    return render_template("notificaciones_admin.html", notificaciones=notificaciones)


# ---------- Gestión de roles ----------
@app.route('/gestion_roles', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def gestion_roles():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        nuevo_rol = request.form.get('rol')

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
    return render_template("administrador/gestion_roles.html", usuarios=usuarios, roles=roles_disponibles)

# ---------- Dashboards ----------
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

# ---------- Cambiar rol ----------

@app.route('/cambiar_rol/<int:user_id>', methods=['POST'])
@login_required
def cambiar_rol(user_id):
    nuevo_rol = request.form['rol']
    usuario = Usuario.query.get(user_id)  # Busca el usuario en la tabla
    
    if usuario:
        usuario.Rol = nuevo_rol  # Cambia el rol
        db.session.commit()      # Guarda cambios en la BD
        flash(f"✅ Rol de {usuario.Nombre} cambiado a {nuevo_rol}", "success")
    else:
        flash("❌ Usuario no encontrado", "danger")
    
    return redirect(url_for('gestion_roles'))

# ------------------ Instalaciones ------------------ #
@app.route('/instalaciones', methods=['GET', 'POST'])
def agendar():
    if request.method == 'POST':
        instalacion = {
            "pedido": request.form['pedido'],
            "producto": request.form['producto'],
            "direccion": request.form['direccion'],
            "fecha": request.form['fecha'],
            "hora": request.form['hora'],
            "comentarios": request.form['comentarios']
        }
        instalaciones.append(instalacion)
        return redirect(url_for('confirmacion'))
    return render_template('instalaciones.html')

@app.route('/confirmacion')
def confirmacion():
    return render_template('confirmacion.html')

@app.route('/lista')
def lista():
    return render_template('lista.html', instalaciones=instalaciones)

if __name__ == '__main__':
    app.run(debug=True)


# ------------------ MAIN ------------------ #
if __name__ == '__main__':
    app.run(debug=True)
