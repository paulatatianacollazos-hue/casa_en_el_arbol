from flask_login import login_required, current_user
from functools import wraps
from flask import redirect, url_for, flash, session

def role_required(*roles):
    """ Decorador para restringir acceso según roles """
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if 'user_id' not in session:
                flash("⚠️ Debes iniciar sesión primero", "warning")
                return redirect(url_for('login'))

            user_rol = session.get("rol", "").lower()
            if user_rol not in [r.lower() for r in roles]:
                flash("❌ No tienes permisos para acceder a esta página", "danger")
                return redirect(url_for('login'))

            return fn(*args, **kwargs)
        return decorated_view
    return wrapper
