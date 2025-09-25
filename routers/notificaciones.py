from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from basedatos.models import db, Notificaciones
from basedatos.decoradores import role_required


notificaciones = Blueprint('notificaciones', __name__, url_prefix='/notificaciones')

# ---------- NOTIFICACIONES_CLIENTE ----------
@notificaciones.route('/', methods=['GET', 'POST'])
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
        return redirect(url_for('notificaciones.ver_notificaciones_cliente'))

    notificaciones = Notificaciones.query.filter_by(
        ID_Usuario=current_user.ID_Usuario
    ).order_by(Notificaciones.Fecha.desc()).all()

    return render_template("notificaciones_cliente.html", notificaciones=notificaciones)


# ---------- NOTIFICACIONES_ADMIN ----------
@notificaciones.route('/admin', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def ver_notificaciones_admin():
    if request.method == 'POST':
        ids = request.form.getlist('ids')
        if not ids:
            flash("❌ No seleccionaste ninguna notificación", "warning")
            return redirect(url_for('notificaciones.ver_notificaciones_admin'))

        try:
            ids_int = [int(i) for i in ids if str(i).isdigit()]
        except ValueError:
            flash("❌ IDs inválidos", "danger")
            return redirect(url_for('notificaciones.ver_notificaciones_admin'))

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

        return redirect(url_for('notificaciones.ver_notificaciones_admin'))

    notificaciones = Notificaciones.query.filter_by(
        ID_Usuario=current_user.ID_Usuario
    ).order_by(Notificaciones.Fecha.desc()).all()

    return render_template("administrador/notificaciones_admin.html", notificaciones=notificaciones)
