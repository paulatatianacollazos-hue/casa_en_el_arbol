from flask import render_template, request, redirect, url_for
from flask import session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_login import login_required, login_user, logout_user
from datetime import datetime, date
from basedatos.models import RegistroSesion, LoginIntento
from basedatos.decoradores import enviar_correo_seguridad



from basedatos.models import db, Usuario
from basedatos.decoradores import validar_password, validar_email
from basedatos.decoradores import send_reset_email
from basedatos.notificaciones import crear_notificacion
from . import auth
from flask_login import current_user


# Serializer
s = URLSafeTimedSerializer("mi_clave_super_secreta_y_unica")


# ------------------ REGISTRO ------------------ #
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre_completo = request.form.get('name', '').strip()
        correo = request.form.get('email', '').strip()
        telefono = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()

        if not nombre_completo or not correo or not password:
            flash('Nombre, correo y contraseña son obligatorios.', 'warning')
            return render_template('register.html', name=nombre_completo,
                                   email=correo, phone=telefono)

        if not validar_email(correo):
            flash('Correo inválido.', 'danger')
            return render_template('register.html', name=nombre_completo,
                                   email=correo, phone=telefono)

        error = validar_password(password)
        if error:
            flash(error, 'danger')
            return render_template('register.html', name=nombre_completo,
                                   email=correo, phone=telefono)

        partes = nombre_completo.split(" ", 1)
        nombre = partes[0]
        apellido = partes[1] if len(partes) > 1 else ""

        if Usuario.query.filter_by(Correo=correo).first():
            flash('Correo ya registrado.', 'danger')
            return render_template('register.html', name=nombre_completo,
                                   email=correo, phone=telefono)

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
                titulo="¡Bienvenido!",
                mensaje="Tu cuenta se ha creado correctamente."
            )

            flash('Cuenta creada. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return render_template('register.html', name=nombre_completo,
                                   email=correo, phone=telefono)

    return render_template('register.html')


# ------------------ LOGIN ------------------ #
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('correo', '').strip()
        password = request.form.get('password', '').strip()

        ip = request.remote_addr
        user_agent = request.headers.get("User-Agent")

        # ⛔ VERIFICAR BLOQUEO
        bloqueo = LoginIntento.query.filter_by(
            email=correo,
            ip=ip,
            user_agent=user_agent,
            bloqueado=True
        ).first()

        if bloqueo:
            flash("Este dispositivo está bloqueado. Revisa tu correo.", "danger")
            return render_template('login.html', correo=correo)

        usuario = Usuario.query.filter_by(Correo=correo).first()

        # ✅ LOGIN CORRECTO
        if usuario and check_password_hash(usuario.Contraseña, password):

            # 🔄 RESETEAR INTENTOS
            intento = LoginIntento.query.filter_by(
                email=correo,
                ip=ip,
                user_agent=user_agent
            ).first()

            if intento:
                intento.intentos = 0
            db.session.commit()

            login_user(usuario)
            flash("Inicio de sesión exitoso", "success")

            # -------- REGISTRO SESIÓN --------
            if usuario.Rol in ['empleado', 'instalador', 'transportista', 'taller']:
                hoy = date.today()
                ahora = datetime.now()

                registro = RegistroSesion.query.filter_by(
                    ID_Usuario=usuario.ID_Usuario,
                    Fecha=hoy
                ).first()

                if not registro:
                    db.session.add(RegistroSesion(
                        ID_Usuario=usuario.ID_Usuario,
                        Fecha=hoy,
                        HoraEntrada=ahora
                    ))
                    db.session.commit()

            session['username'] = f"{usuario.Nombre} {usuario.Apellido or ''}".strip()
            session['show_welcome_modal'] = True

            rutas_por_rol = {
                'admin': 'admin.dashboard',
                'cliente': 'cliente.dashboard',
                'empleado': 'empleado.dashboard',
                'instalador': 'empleado.dashboard',
                'transportista': 'empleado.dashboard',
                'taller': 'empleado.dashboard',
            }

            # 🔹 HISTORIAL LOGIN CORRECTO
            agregar_historial(
                tipo="login_exitoso",
                descripcion=f"Inicio de sesión exitoso para {correo}",
                ubicacion=ip,
                navegador=request.user_agent.browser
            )

            return redirect(url_for(rutas_por_rol.get(usuario.Rol)))

        # ❌ LOGIN FALLIDO → CONTAR INTENTOS
        intento = LoginIntento.query.filter_by(
            email=correo,
            ip=ip,
            user_agent=user_agent
        ).first()

        if not intento:
            intento = LoginIntento(
                email=correo,
                ip=ip,
                user_agent=user_agent,
                intentos=1
            )
            db.session.add(intento)
        else:
            intento.intentos += 1

        db.session.commit()

        # 🔹 HISTORIAL LOGIN FALLIDO
        agregar_historial(
            tipo="login_fallido",
            descripcion=f"Intento de login fallido para {correo}",
            ubicacion=ip,
            navegador=request.user_agent.browser
        )

        # 📧 ENVIAR CORREO AL 3ER INTENTO
        if intento.intentos == 3:
            enviar_correo_seguridad(correo, intento)

        flash("Correo o contraseña incorrectos", "danger")
        return render_template('login.html', correo=correo)

    return render_template('login.html')



# ------------------ LOGOUT ------------------ #

@auth.route('/logout')
@login_required
def logout():
    ip = request.remote_addr
    navegador = request.user_agent.browser

    # ------------------ REGISTRO HORA SALIDA ------------------
    if current_user.Rol in ['empleado', 'instalador', 'transportista', 'taller']:
        hoy = date.today()
        ahora = datetime.now()

        registro = RegistroSesion.query.filter_by(
            ID_Usuario=current_user.ID_Usuario,
            Fecha=hoy,
            HoraSalida=None
        ).first()

        if registro:
            registro.HoraSalida = ahora
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print("❌ ERROR al registrar hora de salida:", e)

    # ------------------ AGREGAR HISTORIAL ------------------
    agregar_historial(
        tipo="logout",
        descripcion=f"Cierre de sesión para {current_user.Correo}",
        ubicacion=ip,
        navegador=navegador
    )

    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('auth.login'))


# ------------------ FORGOT_PASSWORD ------------------ #
@auth.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get("email")
        user = Usuario.query.filter_by(Correo=email).first()
        if user:
            try:
                token = s.dumps(email, salt='password-recovery')
                send_reset_email(user_email=email, user_name=user.Nombre,
                                 token=token)
                flash('Correo enviado.', 'success')
            except Exception as e:
                flash(f'Error: {e}', 'danger')
        else:
            flash('Correo no registrado.', 'warning')
    return render_template("forgot_password.html")


def agregar_historial(tipo, descripcion, ubicacion="Desconocido", navegador="Desconocido"):
    # Crear el historial si no existe
    if "historial" not in session:
        session["historial"] = []

    evento = {
        "tipo": tipo,
        "descripcion": descripcion,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ubicacion": ubicacion,
        "navegador": navegador
    }

    session["historial"].append(evento)
    session.modified = True  # necesario para que Flask guarde cambios en la sesión


@auth.route('/confirmar-dispositivo/<int:intento_id>/<accion>')
def confirmar_dispositivo(intento_id, accion):
    intento = LoginIntento.query.get_or_404(intento_id)

    if accion == 'no':
        intento.bloqueado = True
        db.session.commit()
        return "❌ Dispositivo bloqueado correctamente."

    if accion == 'si':
        return "✅ Dispositivo confirmado. Puedes ignorar este mensaje."

    return "Acción no válida"



# ------------------ RESET_PASSWORD ------------------ #
@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-recovery', max_age=3600)
    except (SignatureExpired, BadSignature):
        flash('Enlace inválido o expirado.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validación: campos completos
        if not new_password or not confirm_password:
            flash('Completa ambos campos.', 'warning')
            return render_template('reset_password.html', token=token)

        # Validación: contraseñas coinciden
        if new_password != confirm_password:
            flash('Las contraseñas no coinciden.', 'warning')
            return render_template('reset_password.html', token=token)

        # Validación de política de seguridad
        error = validar_password(new_password)
        if error:
            flash(error, 'warning')
            return render_template('reset_password.html', token=token)

        # Buscar usuario
        user = Usuario.query.filter_by(Correo=email).first()
        if not user:
            flash('Usuario no encontrado.', 'danger')
            return redirect(url_for('auth.forgot_password'))

        # Actualizar contraseña
        user.Contraseña = generate_password_hash(new_password)
        db.session.commit()

        # Crear notificación
        crear_notificacion(
            user_id=user.ID_Usuario,
            titulo="Contraseña actualizada",
            mensaje="Tu contraseña ha sido cambiada exitosamente."
        )

        flash('Contraseña restablecida correctamente.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', token=token)
