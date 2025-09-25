from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from basedatos.models import db, Usuario
from basedatos.decoradores import role_required, crear_notificacion

roles = Blueprint('roles', __name__, url_prefix='/roles')  


# ---------- GESTION_ROLES ----------
@roles.route('/gestion_roles', methods=['GET', 'POST'])
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

@roles.route('/cambiar_rol/<int:user_id>', methods=['POST'])
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
