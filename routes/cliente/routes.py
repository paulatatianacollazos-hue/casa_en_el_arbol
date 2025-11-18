from flask import (render_template, request, redirect, url_for, flash, session,
                   jsonify, make_response)
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from io import BytesIO
import base64
import os
from sqlalchemy import or_
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from basedatos.db import get_connection
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


@cliente.route('/detalle_pedido/<int:pedido_id>')
@login_required
def detalle_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    cliente = Usuario.query.get(pedido.ID_Usuario)
    empleado = Usuario.query.get(pedido.ID_Empleado
                                 ) if pedido.ID_Empleado else None
    direccion = Direccion.query.filter_by(ID_Usuario=cliente.ID_Usuario
                                          ).first()

    detalles = (
        db.session.query(Detalle_Pedido, Producto)
        .join(Producto, Detalle_Pedido.ID_Producto == Producto.ID_Producto)
        .filter(Detalle_Pedido.ID_Pedido == pedido_id)
        .all()
    )

    productos = [{
        "nombre": prod.NombreProducto,
        "cantidad": det.Cantidad,
        "color": prod.Color or "N/A",
        "material": prod.Material or "N/A"
    } for det, prod in detalles]

    estados = ["pendiente", "en proceso", "en reparto", "entregado"]
    estado_actual = pedido.Estado
    progreso = (estados.index(
        estado_actual) + 1) / len(estados
                                  ) * 100 if estado_actual in estados else 0

    return render_template(
        "cliente/detalle_pedido.html",
        pedido=pedido,
        cliente=cliente,
        empleado=empleado,
        direccion=direccion,
        productos=productos,
        progreso=progreso,
        estado_actual=estado_actual
    )


@cliente.route('/buscar_productos')
def buscar_productos():

    query = request.args.get('q', '')

    try:
        conn = get_connection()                    # ← CORREGIDO
        cursor = conn.cursor(dictionary=True)      # ← AHORA funciona

        sql = """
            SELECT
                p.ID_Producto AS id,
                p.NombreProducto AS nombre,
                p.PrecioUnidad AS precio,
                COALESCE(i.ruta, 'img/default.png') AS imagen
            FROM producto p
            LEFT JOIN imagenproducto i
                ON p.ID_Producto = i.ID_Producto
            WHERE p.NombreProducto LIKE %s
            GROUP BY p.ID_Producto
            LIMIT 20
        """

        cursor.execute(sql, (f"%{query}%",))
        productos = cursor.fetchall()

        cursor.close()
        conn.close()        # ← Muy importante

        return jsonify(productos)

    except Exception as e:
        print("ERROR EN /buscar_productos:", e)
        return jsonify({"error": str(e)}), 500


BASE_KNOWLEDGE = {
    "privacidad": "Tu información está protegida bajo nuestra política de privacidad. Puedes revisarla en la sección correspondiente.",
    "devoluciones": "Puedes solicitar una devolución dentro de los primeros 30 días presentando tu comprobante de compra.",
    "garantía": "Todos nuestros productos cuentan con 1 año de garantía por defectos de fábrica.",
    "empresa": "Somos Casa en el Árbol, diseñamos muebles con identidad y calidad profesional.",
    "soporte": "Nuestro equipo de soporte atiende de lunes a viernes, de 8am a 5pm.",
}

FORBIDDEN_WORDS = ["tarjeta", "credito", "contraseña", "password", "cedula", "documento", "banco", "cuenta"]


# --- MEMORIA CORTA DEL CHAT ---
CONTEXT = {
    "last_question": None
}


# --- RESPUESTAS MÁS HUMANAS ---
def make_response(text):
    """Genera respuestas más naturales para sonar como una IA."""
    neutral = [
        "Entiendo, déjame ayudarte con eso:",
        "Perfecto, esto es lo que puedo decirte:",
        "Claro, aquí tienes la información:",
        "Buena pregunta. Aquí tienes la respuesta:",
    ]

    import random
    return random.choice(neutral) + " " + text


# --- DETECCIÓN DE INTENCIONES ---
def get_intent(message):
    message = message.lower()

    # SaludOs
    if any(w in message for w in ["hola", "buenas", "hey", "saludos"]):
        return make_response("¡Hola! ¿En qué puedo ayudarte hoy?")

    # Agradecimientos
    if any(w in message for w in ["gracias", "te agradezco", "muchas gracias"]):
        return make_response("¡Con gusto! Si necesitas algo más, aquí estoy.")

    # Preguntar precios
    if "precio" in message:
        return make_response("Si deseas saber el precio de un producto, puedes buscarlo directamente en el catálogo o mencionarme el nombre del mueble.")

    # Preguntar productos
    if any(w in message for w in ["tienen", "venden", "producto", "muebles"]):
        return make_response("Sí, contamos con una variedad de productos como salas, dormitorios, comedores y muebles personalizados.")

    # Horarios
    if "horario" in message or "abren" in message or "cierran" in message:
        return make_response("Nuestro horario de atención es de lunes a viernes de 9am a 6pm, y sábados de 10am a 4pm.")

    return None  # No se detectó intención


# --- ENDPOINT IA MEJORADA ---
@cliente.route('/api/chatbot', methods=['POST'])
def chatbot_response():
    user_message = request.json.get("message", "").lower()

    # Palabras prohibidas
    for word in FORBIDDEN_WORDS:
        if word in user_message:
            return jsonify({"response": "Por tu seguridad, no puedo ayudarte con datos personales o sensibles."})

    # Coincidencia exacta con base de conocimiento
    for key, value in BASE_KNOWLEDGE.items():
        if key in user_message:
            CONTEXT["last_question"] = key
            return jsonify({"response": make_response(value)})

    # Intenciones generales
    intent_response = get_intent(user_message)
    if intent_response:
        return jsonify({"response": intent_response})

    # Si no entendió:
    return jsonify({
        "response": "No tengo información específica sobre eso, pero puedo ayudarte con devoluciones, garantías, horarios, productos o políticas."
    })


@cliente.route('/chatbot')
def chatbot():

    return render_template("cliente/chatbot.html")