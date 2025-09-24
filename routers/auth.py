from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import re

from basedatos.models import db, Usuario
from app import mail  

from flask_login import ( login_required, current_user,
    login_user, logout_user
)

auth = Blueprint('auth', __name__, url_prefix='/auth')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre_completo = request.form.get('name', '').strip()
        correo = request.form.get('email', '').strip()
        telefono = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()

        if not nombre_completo or not correo or not password:
            flash('Nombre, correo y contraseña son obligatorios.', 'register_warning')
            return render_template('register.html')

        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres.', 'register_danger')
            return render_template('register.html')

        if not re.search(r"[A-Z]", password):
            flash('La contraseña debe contener al menos una letra mayúscula.', 'register_danger')
            return render_template('register.html')

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            flash('La contraseña debe contener al menos un carácter especial.', 'register_danger')
            return render_template('register.html')

        if re.search(r"(012|123|234|345|456|567|678|789)", password):
            flash('La contraseña no puede contener números consecutivos.', 'register_danger')
            return render_template('register.html')

        partes = nombre_completo.split(" ", 1)
        nombre = partes[0]
        apellido = partes[1] if len(partes) > 1 else ""

        if Usuario.query.filter_by(Correo=correo).first():
            flash('Ya existe una cuenta con ese correo.', 'register_danger')
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

        # Aquí debes tener definida la función crear_notificacion
        crear_notificacion(
            user_id=nuevo_usuario.ID_Usuario,
            titulo="¡Bienvenido a Casa en el Árbol!",
            mensaje="Tu cuenta se ha creado correctamente. Explora nuestros productos y promociones."
        )

        flash('Cuenta creada correctamente, ahora puedes iniciar sesión.', 'register_success')
        return redirect(url_for('auth.login'))

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
