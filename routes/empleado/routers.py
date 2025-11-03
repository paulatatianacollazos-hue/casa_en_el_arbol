from flask import render_template, request, Blueprint, url_for, flash, session
from flask import jsonify, redirect
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from basedatos.models import Usuario, Producto, Calendario, Notificaciones
from basedatos.decoradores import role_required
from basedatos.notificaciones import crear_notificacion
from datetime import datetime
from basedatos.queries import obtener_pedidos_por_cliente
from basedatos.queries import get_productos, get_producto_by_id
from basedatos.models import db, Comentarios, Direccion
import base64
import os


empleado = Blueprint(
    'empleado',
    __name__,
    template_folder='templates',
    url_prefix='/empleado'
)


@empleado.route('/dashboard')
@role_required("transportista")
def dashboard():
    return render_template('empleado/dashboard.html')


@empleado.route('/calendario')
@role_required("transportista")
def calendario():
    return render_template('empleado/calendario.html')


@empleado.route("/actualizacion_datos", methods=["GET", "POST"])
@login_required
@role_required("cliente", "admin")
def actualizacion_datos():

    usuario = current_user
    notificaciones = Notificaciones.query.filter_by(
        ID_Usuario=usuario.ID_Usuario).order_by(
            Notificaciones.Fecha.desc()).all()

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        correo = request.form.get("correo", "").strip()
        password = request.form.get("password", "").strip()

        if not nombre or not apellido or not correo:
            flash("⚠️ Los campos Nombre, Apellido y Correo son obligatorios.",
                  "warning")
        else:
            usuario_existente = Usuario.query.filter(
                Usuario.Correo == correo,
                Usuario.ID_Usuario != usuario.ID_Usuario
            ).first()
            if usuario_existente:
                flash("El correo ya está registrado por otro usuario.",
                      "danger")
            else:
                usuario.Nombre = nombre
                usuario.Apellido = apellido
                usuario.Correo = correo
                if password:
                    usuario.Contraseña = generate_password_hash(password)
                db.session.commit()
                crear_notificacion(
                    user_id=usuario.ID_Usuario,
                    titulo="Perfil actualizado ✏️",
                    mensaje="""Tus datos personales se han actualizado
                    correctamente."""
                )
                flash("✅ Perfil actualizado correctamente", "success")

    return render_template(
        "cliente/actualizacion_datos.html",
        usuario=usuario,
        notificaciones=notificaciones,
    )
