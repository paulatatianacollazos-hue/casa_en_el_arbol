from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from basedatos.queries import guardar_producto, get_productos, get_producto_by_id


from basedatos.models import db, Usuario, Notificaciones ,Direccion
from werkzeug.security import generate_password_hash
from basedatos.decoradores import role_required
from basedatos.notificaciones import crear_notificacion
from basedatos.queries import registrar_pedido
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

@admin.route("/registrar_pedido", methods=["POST"])
def registrar_pedido_route():
    try:
        nombre_comprador = request.form.get("nombreComprador")
        fecha_entrega = request.form.get("fechaEntrega")
        hora_entrega = request.form.get("horaEntrega")
        destino = request.form.get("destino")
        usuario_id = request.form.get("usuarioId", 1)  # puedes ajustar según login

        # Armar lista de productos [{id, cantidad, precio}]
        productos = []
        for prod, cant, prec in zip(
            request.form.getlist("producto[]"),
            request.form.getlist("cantidad[]"),
            request.form.getlist("precio[]"),
        ):
            productos.append({
                "id_producto": prod,
                "cantidad": int(cant),
                "precio": float(prec)
            })

        # Llamar función queries.py
        from basedatos.queries import registrar_pedido
        resultado = registrar_pedido(nombre_comprador, fecha_entrega, hora_entrega, destino, usuario_id, productos)

        return jsonify(resultado)

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

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
    resultados = buscar_pedidos() if request.method == "POST" else []
    return render_template("administrador/reportes_entrega.html", resultados=resultados)

# ---------- ASIGNAR_CALENDARIO ----------
@admin.route("/asignar_calendario", methods=["POST"])
@login_required
@role_required("admin")
def asignar_calendario_route():
    return asignar_calendario_query()


# ---------- ESTADISTICAS ----------
@admin.route("/estadisticas")
@login_required
@role_required("admin")
def estadisticas():
    return render_template("administrador/estadisticas.html")

@admin.route("/actualizacion_datos", methods=["GET", "POST"])
@login_required
@role_required("admin")
def actualizacion_datos():
    usuario = current_user
    direcciones = Direccion.query.filter_by(ID_Usuario=usuario.ID_Usuario).all()
    notificaciones = Notificaciones.query.filter_by(ID_Usuario=usuario.ID_Usuario).order_by(Notificaciones.Fecha.desc()).all()

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        correo = request.form.get("correo", "").strip()
        password = request.form.get("password", "").strip()

        if not nombre or not apellido or not correo:
            flash("⚠️ Los campos Nombre, Apellido y Correo son obligatorios.", "warning")
        else:
            usuario_existente = Usuario.query.filter(
                Usuario.Correo == correo,
                Usuario.ID_Usuario != usuario.ID_Usuario
            ).first()
            if usuario_existente:
                flash("El correo ya está registrado por otro usuario.", "danger")
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
                    mensaje="Tus datos personales se han actualizado correctamente."
                )
                flash("✅ Perfil actualizado correctamente", "success")

    return render_template(
        "administrador/admin_actualizacion_datos.html",
        usuario=usuario,
        direcciones=direcciones,
        notificaciones=notificaciones
    )

@admin.route("/direccion/agregar", methods=["POST"])
@login_required
def agregar_direccion():
    try:
        nueva_direccion = Direccion(
            ID_Usuario=current_user.ID_Usuario,
            Pais="Colombia",
            Departamento="Bogotá, D.C.",
            Ciudad="Bogotá",
            Direccion=request.form.get("direccion"),
            InfoAdicional=request.form.get("infoAdicional"),
            Barrio=request.form.get("barrio"),
            Destinatario=request.form.get("destinatario")
        )
        db.session.add(nueva_direccion)
        db.session.commit()

        crear_notificacion(
            user_id=current_user.ID_Usuario,
            titulo="Dirección agregada 🏠",
            mensaje=f"Se ha agregado una nueva dirección: {nueva_direccion.Direccion}"
        )
        flash("Dirección agregada correctamente 🏠", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error al agregar dirección: {str(e)}", "danger")

    return redirect(url_for("admin_actualizacion_datos"))

@admin.route("/direccion/borrar/<int:id_direccion>", methods=["POST"])
@login_required
def borrar_direccion(id_direccion):
    try:
        direccion = Direccion.query.get_or_404(id_direccion)
        db.session.delete(direccion)
        db.session.commit()

        crear_notificacion(
            user_id=current_user.ID_Usuario,
            titulo="Dirección eliminada 🗑️",
            mensaje=f"La dirección '{direccion.Direccion}' ha sido eliminada."
        )
        flash("Dirección eliminada correctamente 🗑️", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error al eliminar dirección: {str(e)}", "danger")

    return redirect(url_for("admin_actualizacion_datos"))

@admin.route("/catalogo")
@login_required
def catalogo():
    return render_template("administrador/catalogo.html")

@admin.route("/guardar_producto", methods=["POST"])
@login_required
def guardar_producto_route():
    data = request.form
    imagenes = request.files.getlist("imagenes")

    success, msg = guardar_producto(data, imagenes)
    return jsonify({"success": success, "message": msg})

@admin.route("/productos")
@login_required
def mostrar_productos():
    productos = get_productos()
    return render_template("productos/lista.html", productos=productos)


@admin.route("/producto/<int:id_producto>")
@login_required
def detalle_producto(id_producto):
    producto = get_producto_by_id(id_producto)
    return render_template("productos/detalle.html", producto=producto)