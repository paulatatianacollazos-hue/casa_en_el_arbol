from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from flask_login import login_required, current_user

from basedatos.models import db, Usuario, Direccion, Notificaciones
from basedatos.decoradores import role_required, crear_notificacion


auth = Blueprint('actualizacion', __name__, url_prefix='/actualizacion')

# ---------- ACTUALIZACION_DATOS ----------
@auth.route('/actualizacion_datos', methods=['GET', 'POST'])
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


# ---------- DIRECCIONES ----------
@auth.route('/agregar_direccion', methods=['POST'])
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

    return redirect(url_for('actualizacion.actualizacion_datos'))


@auth.route('/borrar_direccion/<int:id_direccion>', methods=['POST'])
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
    return redirect(url_for('actualizacion.actualizacion_datos'))
