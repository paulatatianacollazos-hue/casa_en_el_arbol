from flask import render_template, request, redirect, url_for, flash, session
from flask import jsonify
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
from flask import Blueprint
from flask_login import login_required, current_user
from basedatos.queries import crear_pedido_y_pago

from . import cliente
reviews = []


# ---------- DASHBOARD ----------
@cliente.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')  # viene del login
    return render_template('cliente/dashboard.html', user_id=user_id)


# ---------- FAVORITOS ----------
@cliente.route("/favoritos")
@login_required
def ver_favoritos():
    ids = [int(i) for i in session.get("favorites", []) if str(i).isdigit()]
    productos = Producto.query.filter(Producto.ID_Producto.in_(ids)).all() if ids else []
    return render_template("cliente/favoritos.html", productos=productos)


@cliente.route("/favoritos/add", methods=["POST"])
@login_required
def add_to_favorites():
    data = request.get_json() or {}
    try:
        product_id = int(data.get("id"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "ID inválido"}), 400

    session.setdefault("favorites", [])
    if product_id not in session["favorites"]:
        session["favorites"].append(product_id)
    session.modified = True
    return jsonify({"success": True, "fav_count": len(session["favorites"])})


@cliente.route("/favoritos/remove/<int:product_id>", methods=["POST"])
@login_required
def remove_from_favorites(product_id):
    favs = [int(i) for i in session.get("favorites", []) if str(i).isdigit()]
    if product_id in favs:
        favs.remove(product_id)
        session["favorites"] = favs
        session.modified = True
        flash("Producto eliminado de favoritos", "success")
    return redirect(url_for("cliente.ver_favoritos"))


# ---------- INSTALACIONES ----------
@cliente.route("/instalaciones", methods=["GET", "POST"])
@login_required
def instalaciones_home():
    if request.method == "POST":
        try:
            fecha = datetime.strptime(request.form["fecha"], "%Y-%m-%d").date()
            hora = datetime.strptime(request.form["hora"], "%H:%M").time()
            ubicacion = request.form["ubicacion"]
            tipo = request.form.get("tipo", "Instalación")

            nueva_cita = Calendario(
                Fecha=fecha,
                Hora=hora,
                Ubicacion=ubicacion,
                Tipo=tipo,
                ID_Usuario=current_user.ID_Usuario
            )
            db.session.add(nueva_cita)
            db.session.commit()
            flash("✅ Instalación agendada con éxito", "success")
            return redirect(url_for("cliente.confirmacion_instalacion"))
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error al agendar: {str(e)}", "danger")

    citas = Calendario.query.filter_by(
        ID_Usuario=current_user.ID_Usuario).all()
    return render_template("cliente/instalaciones.html", citas=citas)


@cliente.route("/instalaciones/confirmacion")
@login_required
def confirmacion_instalacion():
    return render_template("cliente/confirmacion.html")


@cliente.route("/instalaciones/lista")
@login_required
def lista_instalaciones():
    citas = Calendario.query.filter_by(
        ID_Usuario=current_user.ID_Usuario).all()
    return render_template("cliente/lista.html", citas=citas)


# ---------- NOTIFICACIONES ----------
@cliente.route("/notificaciones", methods=["GET", "POST"])
@login_required
def ver_notificaciones_cliente():
    if request.method == "POST":
        ids = request.form.getlist("ids")
        if ids:
            try:
                Notificaciones.query.filter(
                    Notificaciones.ID_Usuario == current_user.ID_Usuario,
                    Notificaciones.ID_Notificacion.in_(ids)
                ).delete(synchronize_session=False)
                db.session.commit()
                flash("✅ Notificaciones eliminadas", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"❌ Error al eliminar: {str(e)}", "danger")
        return redirect(url_for("cliente.ver_notificaciones_cliente"))

    notificaciones = Notificaciones.query.filter_by(
        ID_Usuario=current_user.ID_Usuario).order_by(
            Notificaciones.Fecha.desc()).all()
    return render_template("cliente/notificaciones_cliente.html",
                           notificaciones=notificaciones)


# ---------- RESEÑAS ----------
@cliente.route("/reseñas", methods=["GET", "POST"])
@login_required
def resenas():   # <- sin ñ
    if request.method == "POST":
        pedido = request.form["pedido"]
        cliente_nombre = request.form["cliente"]
        estrellas = request.form["estrellas"]
        comentario = request.form["comentario"]
        reviews.append({
            "pedido": pedido,
            "cliente": cliente_nombre,
            "estrellas": estrellas,
            "comentario": comentario
        })
        flash("Reseña añadida con éxito", "success")
        return redirect(url_for("cliente.resenas"))

    avg = round(sum([int(r["estrellas"]) for r in reviews]) / len(
        reviews), 2) if reviews else "N/A"
    return render_template("cliente/reseñas.html", reviews=reviews, avg=avg)


# ---------- ESCRIBIR RESEÑA ----------
@cliente.route("/reseñas/escribir", methods=["GET", "POST"])
@login_required
def escribir_resena():   # <- sin ñ
    if request.method == "POST":
        pedido = request.form["pedido"]
        cliente_nombre = request.form["cliente"]
        estrellas = request.form["estrellas"]
        comentario = request.form["comentario"]

        reviews.append({
            "pedido": pedido,
            "cliente": cliente_nombre,
            "estrellas": estrellas,
            "comentario": comentario
        })

        flash("Reseña añadida con éxito", "success")
        return redirect(url_for("cliente.resenas"))

    return render_template("cliente/escribir.html")


# ---------- PERFIL Y DIRECCIONES ----------
@cliente.route("/actualizacion_datos", methods=["GET", "POST"])
@login_required
@role_required("cliente", "admin")
def actualizacion_datos():

    usuario = current_user
    user_id = usuario.ID_Usuario
    direcciones = Direccion.query.filter_by(
        ID_Usuario=usuario.ID_Usuario).all()
    notificaciones = Notificaciones.query.filter_by(
        ID_Usuario=usuario.ID_Usuario).order_by(
            Notificaciones.Fecha.desc()).all()

    pedidos_con_detalles = obtener_pedidos_por_cliente(user_id)

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
                    mensaje="Tus datos personales se han actualizado correctamente."
                )
                flash("✅ Perfil actualizado correctamente", "success")

    return render_template(
        "cliente/actualizacion_datos.html",
        usuario=usuario,
        direcciones=direcciones,
        notificaciones=notificaciones,
        pedidos_con_detalles=pedidos_con_detalles
    )


@cliente.route("/direccion/agregar", methods=["POST"])
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
            mensaje=f"Se ha agregado una nueva dirección: {
                nueva_direccion.Direccion}"
        )
        flash("Dirección agregada correctamente 🏠", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error al agregar dirección: {str(e)}", "danger")

    return redirect(url_for("cliente.actualizacion_datos"))


@cliente.route("/direccion/borrar/<int:id_direccion>", methods=["POST"])
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

    return redirect(url_for("cliente.actualizacion_datos"))


@cliente.route("/catalogo")
@login_required
def catalogo():
    productos = get_productos()
    return render_template("cliente/cliente_catalogo.html",
                           productos=productos)


@cliente.route("/producto/<int:id_producto>")
@login_required
def detalle_producto(id_producto):
    producto = get_producto_by_id(id_producto)
    if not producto:
        flash("Producto no encontrado", "error")
        return redirect(url_for("admin.catalogo"))
    return render_template("cliente/cliente_detalle.html", producto=producto)


@cliente.route("/firmar/<int:id_pedido>", methods=["GET", "POST"])
@login_required
def firmar_entrega(id_pedido):
    if request.method == "POST":
        # Obtener la imagen de la firma (si se usa canvas)
        firma_base64 = request.form.get("firma")

        if not firma_base64:
            flash("⚠️ Debes firmar antes de confirmar la entrega.", "warning")
            return redirect(url_for("cliente.firmar_entrega",
                                    id_pedido=id_pedido))

        # Guardar la imagen en el servidor (opcional)
        firma_data = base64.b64decode(firma_base64.split(",")[1])
        firma_path = f"static/firmas/firma_{id_pedido}.png"
        os.makedirs(os.path.dirname(firma_path), exist_ok=True)
        with open(firma_path, "wb") as f:
            f.write(firma_data)

        # Crear comentario en la tabla comentarios
        nuevo_comentario = Comentarios(
            ID_Pedido=id_pedido,
            ID_Usuario=current_user.ID_Usuario,
            Texto="El pedido fue entregado y confirmado por el cliente.",
            ImagenFirma=firma_path
        )
        db.session.add(nuevo_comentario)
        db.session.commit()

        flash("✅ Entrega confirmada correctamente.", "success")
        return redirect(url_for("cliente.actualizacion_datos"))

    return render_template("cliente/confirmacion_firma.html",
                           id_pedido=id_pedido)


@cliente.route("/nosotros")
def nosotros():
    return render_template("cliente/Nosotros.html")


# ---------- CARRITO ----------
@cliente.route('/carrito')
def carrito():
    return render_template('cliente/carrito.html')


@cliente.route('/procesar_pago', methods=['POST'])
@login_required
def procesar_pago():
    """
    Endpoint para procesar pagos o pedidos contraentrega.
    """
    data = request.get_json()

    metodo_pago = data.get('metodo_pago')
    destino = data.get('destino', 'Sin dirección')
    items = data.get('items', [])

    if not metodo_pago or not items:
        return jsonify({
            "error": "Faltan datos del pago o los productos."}), 400

    resultado, codigo = crear_pedido_y_pago(current_user, metodo_pago, destino,
                                            items)
    return jsonify(resultado), codigo
