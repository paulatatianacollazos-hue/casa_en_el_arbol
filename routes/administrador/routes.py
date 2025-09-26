from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta

from basedatos.models import db, Usuario, Notificaciones
from basedatos.decoradores import role_required
from basedatos.queries import (
    obtener_todos_los_pedidos,
    detalle,
    obtener_empleados,
    todos_los_pedidos,
    obtener_comentarios_agrupados,
    obtener_productos,
    obtener_producto_por_id,
    buscar_pedidos,
    asignar_empleado as asignar_empleado_query,
    actualizar_pedido as actualizar_pedido_query,
    asignar_calendario as asignar_calendario_query
)

reviews = []

# 🔑 Nombre del blueprint debe ser "admin"
admin = Blueprint("admin", __name__, url_prefix="/admin")

# ---------- DASHBOARD ----------
@admin.route("/")
@login_required
@role_required("admin")
def dashboard():
    return render_template("administrador/admin_dashboard.html")

# ---------- GESTION_ROLES ----------
@admin.route("/gestion_roles", methods=["GET", "POST"])
@login_required
@role_required("admin")
def gestion_roles():
    if request.method == "POST":
        user_id = request.form.get("user_id")
        nuevo_rol = request.form.get("rol")

        usuario = Usuario.query.get(user_id)
        if not usuario:
            flash("❌ Usuario no encontrado", "danger")
            return redirect(url_for("admin.gestion_roles"))

        usuario.Rol = nuevo_rol
        db.session.commit()

        flash(f"✅ Rol de {usuario.Nombre} actualizado a {nuevo_rol}", "success")
        return redirect(url_for("admin.gestion_roles"))

    usuarios = Usuario.query.all()
    roles_disponibles = ["admin", "cliente", "instalador", "transportista"]
    return render_template("administrador/gestion_roles.html", usuarios=usuarios, roles=roles_disponibles)

# ---------- CAMBIAR_ROL ----------
@admin.route("/cambiar_rol/<int:user_id>", methods=["POST"])
@login_required
@role_required("admin")
def cambiar_rol(user_id):
    nuevo_rol = request.form["rol"]
    usuario = Usuario.query.get(user_id)

    if usuario:
        usuario.Rol = nuevo_rol
        db.session.commit()
        flash(f"✅ Rol de {usuario.Nombre} cambiado a {nuevo_rol}", "success")
    else:
        flash("❌ Usuario no encontrado", "danger")

    return redirect(url_for("admin.gestion_roles"))

# ---------- RESEÑAS ----------
@admin.route("/reseñas")
@login_required
@role_required("admin")
def ver_reseñas():
    return render_template("administrador/admin_reseñas.html", reviews=reviews)

# ---------- NOTIFICACIONES ----------
@admin.route("/notificaciones", methods=["GET", "POST"])
@login_required
@role_required("admin")
def ver_notificaciones():
    if request.method == "POST":
        ids = request.form.getlist("ids")
        if not ids:
            flash("❌ No seleccionaste ninguna notificación", "warning")
            return redirect(url_for("admin.ver_notificaciones"))

        try:
            ids_int = [int(i) for i in ids if str(i).isdigit()]
            Notificaciones.query.filter(
                Notificaciones.ID_Usuario == current_user.ID_Usuario,
                Notificaciones.ID_Notificacion.in_(ids_int),
            ).delete(synchronize_session=False)
            db.session.commit()
            flash("✅ Notificaciones eliminadas", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error al eliminar: {e}", "danger")

        return redirect(url_for("admin.ver_notificaciones"))

    notificaciones = Notificaciones.query.filter_by(
        ID_Usuario=current_user.ID_Usuario
    ).order_by(Notificaciones.Fecha.desc()).all()

    return render_template("administrador/notificaciones_admin.html", notificaciones=notificaciones)

# ---------- ENVIOS ----------
@admin.route("/envios")
@login_required
@role_required("admin")
def envios():
    return render_template(
        "administrador/envios.html",
        pedidos=obtener_todos_los_pedidos(),
        detalles=detalle(),
        empleados=obtener_empleados(),
    )

# ---------- CONTROL_PEDIDOS ----------
@admin.route("/control_pedidos")
@login_required
@role_required("admin")
def control_pedidos():
    return render_template("administrador/control_pedidos.html", pedidos=todos_los_pedidos())

# ---------- ASIGNAR_EMPLEADO ----------
@admin.route("/asignar_empleado", methods=["POST"])
@login_required
@role_required("admin")
def asignar_empleado_route():
    data = asignar_empleado_query(request.form)
    return jsonify(data)

# ---------- ACTUALIZAR_PEDIDO ----------
@admin.route("/actualizar_pedido", methods=["POST"])
@login_required
@role_required("admin")
def actualizar_pedido_route():
    actualizar_pedido_query(request.form)
    return redirect(url_for("admin.control_pedidos"))

# ---------- ESTADO ----------
@admin.route("/estado", methods=["GET", "POST"])
@login_required
@role_required("admin")
def estado_pedido():
    if request.method == "POST":
        pedido_id = request.form["pedido_id"]
        return redirect(url_for("admin.control_pedidos", pedido_id=pedido_id))
    return render_template("administrador/estado.html")

# ---------- COMENTARIOS ----------
@admin.route("/comentarios")
@login_required
@role_required("admin")
def mostrar_comentarios():
    return render_template("administrador/comentarios.html", comentarios=obtener_comentarios_agrupados())

# ---------- PRODUCTOS ----------
@admin.route("/productos")
@login_required
@role_required("admin")
def listar_productos():
    return render_template("productos.html", productos=obtener_productos())

@admin.route("/producto/<int:producto_id>")
@login_required
@role_required("admin")
def ver_producto(producto_id):
    producto = obtener_producto_por_id(producto_id)
    if not producto:
        return "Producto no encontrado", 404
    return render_template("detalles.html", producto=producto)

# ---------- REPORTES ----------
@admin.route("/reporte", methods=["GET", "POST"])
@login_required
@role_required("admin")
def reporte_pedidos():
    resultados = buscar_pedidos(request.form) if request.method == "POST" else []
    return render_template("administrador/reportes_entrega.html", resultados=resultados)

# ---------- ASIGNAR_CALENDARIO ----------
@admin.route("/asignar_calendario", methods=["POST"])
@login_required
@role_required("admin")
def asignar_calendario_route():
    return jsonify(asignar_calendario_query(request.form))

# ---------- ESTADISTICAS ----------
@admin.route("/estadisticas")
@login_required
@role_required("admin")
def estadisticas():
    return render_template("administrador/estadisticas.html")
