from functools import wraps
from flask import redirect, url_for, flash, render_template
from flask_login import current_user
import re
from flask_mail import Message
from extensions import mail
from flask import current_app
from datetime import datetime


def role_required(*roles):
    """
    Decorador para restringir acceso según roles.

    Uso:
        @role_required('instalador', 'admin')
    """
    # Convertimos todos los roles permitidos a minúsculas
    valid_roles = [r.strip().lower() for r in roles]

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Verificar si el usuario está autenticado
            if not current_user.is_authenticated:
                flash("⚠️ Debes iniciar sesión primero", "warning")
                return redirect(url_for('auth.login'))

            # Obtener el rol del usuario, manejar None o cadena vacía
            user_role = getattr(current_user, 'Rol', None)
            if not user_role or not user_role.strip():
                flash("❌ Tu cuenta no tiene un rol válido", "danger")
                return redirect(url_for('auth.login'))

            # Normalizar el rol a minúsculas
            user_role = user_role.strip().lower()

            # Verificar si el rol del usuario está entre los permitidos
            if user_role not in valid_roles:
                flash("❌ No tienes permisos para acceder a esta página",
                      "danger")
                return redirect(url_for('auth.login'))

            # Todo correcto, ejecutar la función original
            return fn(*args, **kwargs)

        return wrapper
    return decorator


def validar_password(password):
    """Valida que la contraseña cumpla con las políticas de seguridad."""
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
    """Valida formato básico de email."""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)


def send_reset_email(user_email, user_name, token):
    # Generar URL de recuperación de contraseña
    reset_url = url_for('auth.reset_password', token=token, _external=True)

    # Crear el mensaje con HTML
    msg = Message(
        subject="Recuperación de contraseña - Casa en el Árbol",
        recipients=[user_email]
    )

    # Renderizamos la plantilla HTML con tus estilos
    msg.html = render_template(
        'email_reset.html',
        # Asegúrate de tener esta plantilla en templates/email/
        user_name=user_name,
        reset_url=reset_url
    )

    # Enviar el correo
    mail.send(msg)


def enviar_correo_seguridad(email, intento):

    with current_app.app_context():
        msg = Message(
            subject="⚠️ Alerta de seguridad - Casa en el Árbol",
            recipients=[email]
        )

        msg.html = render_template(
            "email_seguridad.html",
            intentos=intento.intentos,
            ip=intento.ip,
            fecha=intento.fecha,
            intento_id=intento.id
        )

        mail.send(msg)


def enviar_factura_email(usuario, pedido, productos):
    """
    Envía la factura del pedido por correo
    """
    with current_app.app_context():
        msg = Message(
            subject=f"🧾 Factura de tu pedido #{pedido.id}",
            recipients=[usuario.Correo]
        )

        msg.html = render_template(
            "email_factura.html",
            usuario=usuario,
            pedido=pedido,
            productos=productos,
            fecha=datetime.now()
        )

        mail.send(msg)