from flask import (render_template, request, redirect, url_for, flash, session,
                   jsonify, make_response)
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from io import BytesIO
import base64
import os

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from basedatos.models import (
    db, Usuario, Producto, Calendario, Notificaciones,
    Detalle_Pedido, Comentarios, Direccion, Pedido, ImagenProducto, Categorias,
    Reseñas
)
from basedatos.decoradores import role_required
from basedatos.notificaciones import crear_notificacion
from basedatos.queries import (
    obtener_pedidos_por_cliente,
    get_productos,
    get_producto_by_id,
    recivo,
    crear_pedido_y_pago
)

from . import cliente

# listas compartidas
mensajes = []
reviews = []


# ---------- DASHBOARD ----------
@cliente.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')  # viene del login
    return render_template('cliente/dashboard.html', user_id=user_id)


# ---------- INSTALACIONES ----------
# Mostrar las instalaciones
@cliente.route('/instalaciones', methods=['GET'])
def instalaciones():
    calendarios = Calendario.query.all()  # O filtra por usuario
    return render_template('cliente/instalaciones.html',
                           calendarios=calendarios)


# Actualizar instalación
@cliente.route('/instalaciones/actualizar', methods=['POST'])
def actualizar_instalacion():
    id_pedido = request.form.get('id_pedido')
    nueva_fecha = request.form.get('fecha_entrega')
    nueva_hora = request.form.get('hora_entrega')  # opcional

    # 1️⃣ Validar campos obligatorios
    if not id_pedido or not nueva_fecha:
        flash("Debes ingresar todos los datos obligatorios.", "instalaciones-danger")
        return redirect(url_for('cliente.instalaciones'))

    # 2️⃣ Validar que el pedido existe y pertenece al usuario
    pedido = Pedido.query.get(id_pedido)
    if not pedido:
        flash("El pedido no existe.", "instalaciones-danger")
        return redirect(url_for('cliente.instalaciones'))
    if pedido.ID_Usuario != current_user.id:
        flash("No puedes modificar un pedido que no es tuyo.", "instalaciones-warning")
        return redirect(url_for('cliente.instalaciones'))

    # 3️⃣ Buscar calendario asociado al pedido
    calendario = Calendario.query.filter_by(ID_Pedido=id_pedido).first()
    if not calendario:
        flash("No se encontró un calendario para este pedido.", "instalaciones-warning")
        return redirect(url_for('cliente.instalaciones'))

    # 4️⃣ Convertir fecha y hora
    try:
        fecha_dt = datetime.strptime(nueva_fecha, "%Y-%m-%d").date()
        hora_dt = datetime.strptime(nueva_hora, "%H:%M").time() if nueva_hora else calendario.Hora
    except ValueError:
        flash("Formato de fecha u hora inválido.", "instalaciones-danger")
        return redirect(url_for('cliente.instalaciones'))

    # 5️⃣ Determinar intervalo según tipo
    intervalo = timedelta(minutes=60 if calendario.Tipo == "Instalación" else 30)
    nueva_datetime = datetime.combine(fecha_dt, hora_dt)
    inicio_intervalo = nueva_datetime - intervalo
    fin_intervalo = nueva_datetime + intervalo

    # 6️⃣ Validar conflictos de horarios
    otros_eventos = Calendario.query.filter(
        Calendario.Fecha == fecha_dt,
        Calendario.ID_Calendario != calendario.ID_Calendario
    ).all()

    for evento in otros_eventos:
        if not evento.Hora:
            continue
        evento_datetime = datetime.combine(evento.Fecha, evento.Hora)
        evento_intervalo = timedelta(
            minutes=60 if evento.Tipo == "Instalación" else 30)
        if (inicio_intervalo <= evento_datetime <= fin_intervalo):
            flash(f"Conflicto con otro evento ({evento.Tipo}) a las {evento.Hora.strftime('%H:%M')}. Elige otra hora.", "instalaciones-warning")
            return redirect(url_for('cliente.instalaciones'))

    # 7️⃣ Actualizar calendario
    calendario.Fecha = fecha_dt
    calendario.Hora = hora_dt
    calendario.Tipo = "Instalación"

    try:
        db.session.add(calendario)
        db.session.commit()
        flash("Calendario actualizado correctamente.", "instalaciones-success")
    except Exception as e:
        db.session.rollback()
        print("Error al actualizar calendario:", e)
        flash("Ocurrió un error al actualizar el calendario.", "instalaciones-danger")

    return redirect(url_for('cliente.instalaciones'))


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
@cliente.route("/guardar_reseña_pedido/<int:id_pedido>", methods=["POST"])
@login_required
def guardar_reseña_pedido(id_pedido):
    comentario = request.form.get("comentario")
    estrellas = request.form.get("estrellas")

    if not comentario or not estrellas:
        flash("Por favor, completa todos los campos.", "error")
        return redirect(url_for("cliente.actualizacion_datos"))

    reseña = Reseñas.query.filter_by(
        ID_Usuario=current_user.ID_Usuario,
        ID_Referencia=id_pedido,
        tipo="pedido"
    ).first()

    if reseña:
        reseña.Comentario = comentario
        reseña.Estrellas = int(estrellas)
        reseña.Fecha = datetime.utcnow()
        mensaje = "Reseña actualizada correctamente."
    else:
        nueva_reseña = Reseñas(
            ID_Usuario=current_user.ID_Usuario,
            ID_Referencia=id_pedido,
            tipo="pedido",
            Comentario=comentario,
            Estrellas=int(estrellas)
        )
        db.session.add(nueva_reseña)
        mensaje = "Reseña guardada correctamente."

    db.session.commit()
    flash(mensaje, "success")
    return redirect(url_for("cliente.actualizacion_datos"))


# ---------- ESCRIBIR RESEÑA ----------
@cliente.route("/producto/<int:id_producto>/reseña", methods=["POST"])
@login_required
def guardar_reseña_producto(id_producto):
    producto = get_producto_by_id(id_producto)
    if not producto:
        flash("Producto no encontrado", "error")
        return redirect(url_for("cliente.catalogo"))

    comentario = request.form.get("comentario")
    estrellas = request.form.get("estrellas")

    if not comentario or not estrellas:
        flash("Por favor completa todos los campos.", "error")
        return redirect(url_for("cliente.detalle_producto",
                                id_producto=id_producto))

    nueva_reseña = Reseñas(
        ID_Usuario=current_user.ID_Usuario,
        ID_Referencia=id_producto,
        tipo="producto",  # 🔹 Importante
        Comentario=comentario,
        Estrellas=int(estrellas)
    )

    db.session.add(nueva_reseña)
    db.session.commit()

    flash("Gracias por dejar tu reseña ❤️", "success")
    return redirect(url_for("cliente.detalle_producto",
                            id_producto=id_producto))


# ---------- PERFIL Y DIRECCIONES ----------
@cliente.route("/actualizacion_datos", methods=["GET", "POST"])
@login_required
@role_required("cliente", "admin")
def actualizacion_datos():
    usuario = current_user
    user_id = usuario.ID_Usuario

    # 📦 Direcciones y notificaciones del usuario
    direcciones = Direccion.query.filter_by(ID_Usuario=user_id).all()
    notificaciones = Notificaciones.query.filter_by(ID_Usuario=user_id).order_by(Notificaciones.Fecha.desc()).all()

    # 🧾 Obtener pedidos con sus detalles (usa tu función personalizada)
    pedidos_con_detalles = obtener_pedidos_por_cliente(user_id)

    # 🧩 Para cada pedido, buscar si tiene reseña tipo "pedido"
    for pedido in pedidos_con_detalles:
        reseña = Reseñas.query.filter_by(
            ID_Usuario=user_id,
            ID_Referencia=pedido["ID_Pedido"],  # referencia al ID del pedido
            tipo="pedido"
        ).first()
        pedido["reseña"] = reseña  # ← Esto permite usar item.reseña en el HTML

    # 🧠 Si el método es POST, actualizar datos del usuario
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

    # 🧾 Renderizar la vista con toda la información
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
        return redirect(url_for("cliente.catalogo"))

    # Verificar si el usuario compró este producto
    ha_comprado = (
        db.session.query(Detalle_Pedido)
        .join(Pedido, Detalle_Pedido.ID_Pedido == Pedido.ID_Pedido)
        .filter(
            Pedido.ID_Usuario == current_user.ID_Usuario,
            Detalle_Pedido.ID_Producto == id_producto
        )
        .first() is not None
    )

    # 🟢 Traer reseñas tipo "producto"
    reseñas = Reseñas.query.filter_by(
        ID_Referencia=id_producto,
        tipo="producto"
    ).order_by(Reseñas.Fecha.desc()).all()

    return render_template(
        "cliente/cliente_detalle.html",
        producto=producto,
        ha_comprado=ha_comprado,
        reseñas=reseñas
    )


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


@cliente.route('/pagos')
def pagos():
    return render_template('cliente/pagos.html')


@cliente.route('/confirmar_pago', methods=['POST'])
@login_required
def confirmar_pago():
    data = request.get_json()
    print("📦 Datos recibidos:", data)

    metodo_pago = data.get("metodo_pago")
    productos = data.get("productos", [])
    total = data.get("total", 0)

    print("🎭 Rol actual:", getattr(current_user, "rol", "Desconocido"))

    try:
        pedido_id = crear_pedido_y_pago(
            id_usuario=current_user.id,
            carrito=productos,
            metodo_pago=metodo_pago,
            monto_total=total,
            destino="Dirección registrada"
        )

        if pedido_id:
            print("✅ Pedido creado con ID:", pedido_id)
            return jsonify({"success": True, "pedido_id": pedido_id}), 200
        else:
            print("⚠️ No se pudo crear el pedido")
            return jsonify({"success": False, "error":
                            "Error al crear el pedido"}), 500

    except Exception as e:
        print("💥 Error en confirmar_pago:", e)
        return jsonify({"success": False, "error": str(e)}), 500


@cliente.route('/factura/pdf/<int:pedido_id>', methods=['GET'])
@login_required
def factura_pdf(pedido_id):
    try:
        datos = recivo(pedido_id)
        usuario = current_user

        # 🧾 Creamos PDF en memoria
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        pdf.setTitle(f"Factura_{pedido_id}")

        # 🔹 Encabezado
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(200, 750, "CASA EN EL ÁRBOL - FACTURA")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, 730,
                       f"Cliente: {usuario.Nombre} {usuario.Apellido}")
        pdf.drawString(50, 715, f"Correo: {usuario.Correo}")
        pdf.drawString(50, 700, f"ID Pedido: {pedido_id}")

        # 🔹 Cabecera de tabla
        y = 670
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(50, y, "Producto")
        pdf.drawString(200, y, "Cant.")
        pdf.drawString(250, y, "Precio")
        pdf.drawString(320, y, "Método")
        pdf.drawString(400, y, "Monto")
        pdf.drawString(470, y, "Fecha")
        y -= 20

        # 🔹 Contenido
        pdf.setFont("Helvetica", 9)
        for f in datos:
            pdf.drawString(50, y, f["NombreProducto"])
            pdf.drawString(200, y, str(f["cantidad"]))
            pdf.drawString(250, y, f"${f['PrecioUnidad']}")
            pdf.drawString(320, y, f["MetodoPago"])
            pdf.drawString(400, y, f"${f['Monto']}")
            pdf.drawString(470, y, str(f["FechaPago"]))
            y -= 15

        pdf.save()
        buffer.seek(0)

        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'
                         ] = f'inline; filename=factura_{pedido_id}.pdf'
        return response

    except Exception as e:
        print("❌ Error generando PDF:", e)
        return jsonify({"error": str(e)}), 500


# ---------- FAVORITOS ----------
@cliente.route('/favoritos')
@login_required
def favoritos():
    key = f"favoritos_{current_user.ID_Usuario}"
    favoritos_ids = session.get(key, [])

    productos = []
    if favoritos_ids:
        productos = Producto.query.filter(Producto.ID_Producto.in_(
            favoritos_ids)).all()

    return render_template("cliente/favoritos.html", productos=productos)


@cliente.route('/favorito/toggle/<int:producto_id>', methods=['POST'])
@login_required
def toggle_favorito(producto_id):
    # Crea una clave única por usuario en la sesión
    key = f"favoritos_{current_user.ID_Usuario}"

    # Obtiene la lista de favoritos del usuario (si no existe, crea una lista vacía)
    favoritos = session.get(key, [])

    # Agrega o quita el producto según corresponda
    if producto_id in favoritos:
        favoritos.remove(producto_id)
        accion = 'eliminado'
    else:
        favoritos.append(producto_id)
        accion = 'agregado'

    # Guarda la lista actualizada en la sesión
    session[key] = favoritos
    session.modified = True

    return jsonify({'accion': accion})



# Comparación de productos

@cliente.route('/comparar', methods=['GET', 'POST'])
@login_required
def comparar_productos():
    # Obtener todos los productos con su imagen
    productos = db.session.query(Producto, Categorias, ImagenProducto.ruta).\
        join(Categorias, Producto.ID_Categoria == Categorias.ID_Categoria).\
        outerjoin(ImagenProducto, Producto.ID_Producto == ImagenProducto.ID_Producto).all()

    seleccionados = []

    if request.method == 'POST':
        seleccion = request.form.getlist('productos')
        if len(seleccion) > 3:
            flash('Solo puedes comparar un máximo de 3 productos.', 'warning')
        elif len(seleccion) == 0:
            flash('Debes seleccionar al menos un producto.', 'warning')
        else:
            seleccionados = db.session.query(Producto, Categorias, ImagenProducto.ruta).\
                join(Categorias, Producto.ID_Categoria == Categorias.ID_Categoria).\
                outerjoin(ImagenProducto, Producto.ID_Producto == ImagenProducto.ID_Producto).\
                filter(Producto.ID_Producto.in_(seleccion)).all()

    return render_template('cliente/comparar.html',
                           productos=productos,
                           seleccionados=seleccionados)


# ------------------ RUTAS DEL CHAT ------------------
@cliente.route('/chat')
@login_required
def chat_cliente():
    return render_template('common/chat.html', usuario='Cliente')

@cliente.route('/enviar_mensaje', methods=['POST'])
@login_required
def enviar_mensaje_cliente():
    data = request.get_json()
    mensajes.append({'usuario': 'Cliente', 'texto': data.get('texto'), 'fecha': datetime.now().isoformat()})
    return jsonify({'ok': True})

@cliente.route('/obtener_mensajes')
@login_required
def obtener_mensajes_cliente():
    return jsonify(mensajes)


@cliente.route('/factura/<int:pedido_id>', methods=['GET'])
@login_required
def obtener_factura(pedido_id):
    """
    Devuelve en JSON los detalles de una factura específica
    para el pedido indicado.
    """
    try:
        datos = recivo(pedido_id)  # ← esta función ya la usas en factura_pdf
        if not datos:
            return jsonify({"error": "Factura no encontrada"}), 404

        return jsonify(datos)

    except Exception as e:
        print("❌ Error al obtener factura:", e)
        return jsonify({"error": "Error interno del servidor"}), 500
