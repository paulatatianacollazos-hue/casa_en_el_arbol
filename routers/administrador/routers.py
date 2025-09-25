from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from basedatos.models import db, Usuario, Notificaciones
from basedatos.decoradores import role_required, crear_notificacion

reviews = []

admin = Blueprint('admin', __name__, url_prefix='/admin')  

# ---------- DASHBOARDS ----------
@admin.route('/admin')
@login_required
@role_required('admin')
def admin_dashboard():
    return render_template('administrador/admin_dashboard.html')


# ---------- GESTION_ROLES ----------
@admin.route('/gestion_roles', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def gestion_roles():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        nuevo_rol = request.form.get('rol')

        usuario = Usuario.query.get(user_id)
        if not usuario:
            flash("❌ Usuario no encontrado", "danger")
            return redirect(url_for('roles.gestion_roles'))  

        usuario.Rol = nuevo_rol
        db.session.commit()

        flash(f"✅ Rol de {usuario.Nombre} actualizado a {nuevo_rol}", "success")
        return redirect(url_for('roles.gestion_roles')) 

    usuarios = Usuario.query.all()
    roles_disponibles = ["admin", "cliente", "instalador", "transportista"]
    return render_template("administrador/gestion_roles.html", usuarios=usuarios, roles=roles_disponibles)

# ---------- CAMBIAR_ROL----------

@admin.route('/cambiar_rol/<int:user_id>', methods=['POST'])
@login_required
def cambiar_rol(user_id):
    nuevo_rol = request.form['rol']
    usuario = Usuario.query.get(user_id)  
    
    if usuario:
        usuario.Rol = nuevo_rol  
        db.session.commit()      
        flash(f"✅ Rol de {usuario.Nombre} cambiado a {nuevo_rol}", "success")
    else:
        flash("❌ Usuario no encontrado", "danger")
    
    return redirect(url_for('gestion_roles'))

# ---------- RESEÑAS----------
@admin.route('/admin')
@login_required
def admin():
    
    return render_template("administrador/admin_reseñas.html", reviews=reviews)

# ---------- NOTIFICACIONES_ADMIN ----------
@admin.route('/admin', methods=['GET', 'POST'])
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