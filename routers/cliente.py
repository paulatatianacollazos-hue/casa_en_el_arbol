from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from basedatos.models import db, Usuario, Producto , Calendario, Notificaciones, Direccion
from datetime import datetime

from basedatos.decoradores import role_required, crear_notificacion

reviews = []

cliente = Blueprint('cliente', __name__, url_prefix='/cliente')

# ---------- DASHBOARD ----------

@cliente.route('/cliente')
@login_required
@role_required('cliente')
def dashboard():
    return render_template('dashboard.html')

@cliente.route("/add", methods=["POST"])
def add_to_cart():
    data = request.get_json()

    try:
        product_id = int(data.get("id"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "ID inválido"}), 400

    if "cart" not in session:
        session["cart"] = []

    if product_id not in session["cart"]:
        session["cart"].append(product_id)

    session.modified = True

    return jsonify({
        "success": True,
        "cart_count": len(session["cart"])
    })


# ---------- AÑADIR_AL_CARRITO ----------

@cliente.route("/", methods=["GET"])
def ver_carrito():
    ids = session.get("cart", [])

    try:
        ids = [int(i) for i in ids]
    except:
        ids = []

    productos = Producto.query.filter(Producto.ID_Producto.in_(ids)).all() if ids else []

    print("🛒 Productos encontrados:", [p.NombreProducto for p in productos])

    return render_template("carrito.html", productos=productos)

# ---------- ELIMINAR_DEL_CARRITO----------


@cliente.route("/remove/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id):
    cart = session.get("cart", [])

    try:
        cart = [int(i) for i in cart]
    except:
        pass

    if product_id in cart:
        cart.remove(product_id)
        session["cart"] = cart
        session.modified = True
        flash("Producto eliminado del carrito", "success")

    return redirect(url_for("carrito.ver_carrito"))


# ---------- AÑADIR_FAVORITOS----------

@cliente.route("/add_to_favorites", methods=["POST"])
def add_to_favorites():
    data = request.get_json() or {}
    try:
        product_id = int(data.get("id"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "ID inválido"}), 400

    if "favorites" not in session:
        session["favorites"] = []

    favs = list(map(int, session.get("favorites", [])))
    if product_id not in favs:
        favs.append(product_id)

    session["favorites"] = favs
    session.modified = True

    return jsonify({"success": True, "fav_count": len(session["favorites"])})

# ---------- VER_FAVORITOS----------

@cliente.route("/")
def ver_favoritos():  
    ids = session.get("favorites", [])
    try:
        ids_int = [int(i) for i in ids]
    except Exception:
        ids_int = []

    productos = Producto.query.filter(Producto.ID_Producto.in_(ids_int)).all() if ids_int else []
    return render_template("favoritos.html", productos=productos)


# ---------- ELIMINAR_FAVORITOS----------
@cliente.route("/remove_from_favorites/<int:product_id>", methods=["POST"])
def remove_from_favorites(product_id):
    favs = session.get("favorites", [])
    try:
        favs = [int(i) for i in favs]
    except:
        pass

    if product_id in favs:
        favs.remove(product_id)
        session["favorites"] = favs
        session.modified = True
        flash("Producto eliminado de favoritos", "success")

    return redirect(url_for("favoritos.ver_favoritos"))

# ---------- AGENDAR_INSTALACIONES ----------
@cliente.route('/', methods=['GET', 'POST'])
@login_required
def instalaciones_home():
    if request.method == 'POST':
        fecha = datetime.strptime(request.form['fecha'], "%Y-%m-%d").date()
        hora = datetime.strptime(request.form['hora'], "%H:%M").time()
        ubicacion = request.form['ubicacion']
        tipo = request.form.get('tipo', 'Instalación')

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
        return redirect(url_for('instalaciones.confirmacion'))

    citas = Calendario.query.filter_by(ID_Usuario=current_user.ID_Usuario).all()
    return render_template("instalaciones.html", citas=citas)

# ----------CONFIRMACION_INSTALACIONES----------
@cliente.route('/confirmacion')
@login_required
def confirmacion():
    return render_template("confirmacion.html")

# ---------- LISTA_INSTALACIONES ----------

@cliente.route('/lista')
@login_required
def lista():
    citas = Calendario.query.filter_by(ID_Usuario=current_user.ID_Usuario).all()
    return render_template("lista.html", citas=citas)

# ---------- NOTIFICACIONES_CLIENTE ----------
@cliente.route('/', methods=['GET', 'POST'])
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

# ---------- RESEÑAS ----------

@cliente.route('/reseñas')
def reseñas():
    if reviews:
        avg = round(sum([int(r['estrellas']) for r in reviews]) / len(reviews), 2)
    else:
        avg = "N/A"
    return render_template("reseñas.html", reviews=reviews, avg=avg)

# ---------- ESCRIBIR_RESEÑAS ----------

@cliente.route('/escribir', methods=['GET', 'POST'])
@login_required
def escribir():
    if request.method == 'POST':
        pedido = request.form['pedido']
        cliente = request.form['cliente']
        estrellas = request.form['estrellas']
        comentario = request.form['comentario']
        reviews.append({"pedido": pedido, "cliente": cliente, "estrellas": estrellas, "comentario": comentario})
        flash("Reseña añadida con éxito", "success")
        return redirect(url_for('reseña.reseñas'))
    return render_template("escribir.html")

# ---------- ACTUALIZACION_DATOS ----------
@cliente.route('/actualizacion_datos', methods=['GET', 'POST'])
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
@cliente.route('/agregar_direccion', methods=['POST'])
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


@cliente.route('/borrar_direccion/<int:id_direccion>', methods=['POST'])
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
