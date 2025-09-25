from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from basedatos.models import db, Usuario, Producto, Calendario, Notificaciones, Direccion
from basedatos.decoradores import role_required, crear_notificacion
from datetime import datetime

cliente = Blueprint("cliente", __name__, url_prefix="/cliente")
reviews = []

# ---------- DASHBOARD ----------
@cliente.route("/dashboard")
@login_required
@role_required("cliente")
def dashboard():
    return render_template("cliente/dashboard.html")

# ---------- CARRITO ----------
@cliente.route("/carrito")
@login_required
def ver_carrito():
    ids = [int(i) for i in session.get("cart", []) if str(i).isdigit()]
    productos = Producto.query.filter(Producto.ID_Producto.in_(ids)).all() if ids else []
    return render_template("cliente/carrito.html", productos=productos)

@cliente.route("/carrito/add", methods=["POST"])
@login_required
def add_to_cart():
    data = request.get_json()
    try:
        product_id = int(data.get("id"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "ID inválido"}), 400

    session.setdefault("cart", [])
    if product_id not in session["cart"]:
        session["cart"].append(product_id)
    session.modified = True
    return jsonify({"success": True, "cart_count": len(session["cart"])})

@cliente.route("/carrito/remove/<int:product_id>", methods=["POST"])
@login_required
def remove_from_cart(product_id):
    cart = [int(i) for i in session.get("cart", []) if str(i).isdigit()]
    if product_id in cart:
        cart.remove(product_id)
        session["cart"] = cart
        session.modified = True
        flash("Producto eliminado del carrito", "success")
    return redirect(url_for("cliente.ver_carrito"))

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

    citas = Calendario.query.filter_by(ID_Usuario=current_user.ID_Usuario).all()
    return render_template("cliente/instalaciones.html", citas=citas)

@cliente.route("/instalaciones/confirmacion")
@login_required
def confirmacion_instalacion():
    return render_template("cliente/confirmacion.html")

@cliente.route("/instalaciones/lista")
@login_required
def lista_instalaciones():
    citas = Calendario.query.filter_by(ID_Usuario=current_user.ID_Usuario).all()
    return render_template("cliente/lista.html", citas=citas)

# ---------- NOTIFICACIONES ----------
@cliente.route("/notificaciones", methods=["GET", "POST"])
@login_required
def ver_notificaciones_cliente():
    if request.method == "POST":
        ids = request.form.getlist("ids")
        if ids:
            Notificaciones.query.filter(
                Notificaciones.ID_Usuario == current_user.ID_Usuario,
                Notificaciones.ID_Notificacion.in_(ids)
            ).delete(synchronize_session=False)
            db.session.commit()
            flash("✅ Notificaciones eliminadas", "success")
        return redirect(url_for("cliente.ver_notificaciones_cliente"))

    notificaciones = Notificaciones.query.filter_by(ID_Usuario=current_user.ID_Usuario).order_by(Notificaciones.Fecha.desc()).all()
    return render_template("cliente/notificaciones_cliente.html", notificaciones=notificaciones)

# ---------- RESEÑAS ----------
@cliente.route("/reseñas", methods=["GET", "POST"])
@login_required
def reseñas():
    if request.method == "POST":
        pedido = request.form["pedido"]
        cliente_nombre = request.form["cliente"]
        estrellas = request.form["estrellas"]
        comentario = request.form["comentario"]
        reviews.append({"pedido": pedido, "cliente": cliente_nombre, "estrellas": estrellas, "comentario": comentario})
        flash("Reseña añadida con éxito", "success")
        return redirect(url_for("cliente.reseñas"))

    avg = round(sum([int(r["estrellas"]) for r in reviews]) / len(reviews), 2) if reviews else "N/A"
    return render_template("cliente/reseñas.html", reviews=reviews, avg=avg)

# ---------- PERFIL Y DIRECCIONES ----------
@cliente.route("/actualizacion_datos", methods=["GET", "POST"])
@login_required
@role_required("cliente", "instalador", "transportista", "admin")
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

    return render_template("cliente/Actualizacion_datos.html",
                           usuario=usuario,
                           direcciones=direcciones,
                           notificaciones=notificaciones)

@cliente.route("/direccion/agregar", methods=["POST"])
@login_required
def agregar_direccion():
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

    return redirect(url_for("cliente.actualizacion_datos"))

@cliente.route("/direccion/borrar/<int:id_direccion>", methods=["POST"])
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
    return redirect(url_for("cliente.actualizacion_datos"))
