from flask import render_template, request, redirect, url_for, flash, session
from flask import jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from basedatos.models import Usuario, Producto, Calendario, Notificaciones
from basedatos.decoradores import role_required
from basedatos.notificaciones import crear_notificacion
from datetime import datetime
from basedatos.queries import obtener_pedidos_por_cliente
from basedatos.queries import get_productos, get_producto_by_id, recivo
from basedatos.models import db, Comentarios, Direccion
from basedatos.models import Pedido, Seguimiento
import base64
import os
from basedatos.queries import crear_pedido_y_pago
from flask import make_response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

from . import cliente
reviews = []


# ---------- DASHBOARD ----------
@cliente.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')  # viene del login
    return render_template('cliente/dashboard.html', user_id=user_id)


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
                    mensaje="""Tus datos personales se han actualizado
                    correctamente."""
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


@cliente.route('/seguimiento/<int:pedido_id>')
def seguimiento(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    seg = Seguimiento.query.filter_by(pedido_id=pedido_id).order_by(
        Seguimiento.timestamp.desc()).first()
    return render_template('seguimiento.html', pedido=pedido, seguimiento=seg)


@cliente.route('/api/posicion/<int:pedido_id>')
def api_posicion(pedido_id):
    seg = Seguimiento.query.filter_by(pedido_id=pedido_id).order_by(
        Seguimiento.timestamp.desc()).first()
    if not seg:
        return jsonify({'ok': False, 'message': 'No hay seguimiento'}), 404
    return jsonify({'ok': True, 'lat': seg.lat, 'lng': seg.lng, 'estado':
                    seg.estado, 'timestamp': seg.timestamp.isoformat()})


# ---------- FAVORITOS ----------
@cliente.route('/favorito/<int:producto_id>', methods=['POST'])
@login_required
def favorito(producto_id):
    favoritos = session.get('favoritos', {})

    user_id_str = str(current_user.id)
    user_favs = favoritos.get(user_id_str, [])

    if producto_id in user_favs:
        user_favs.remove(producto_id)
        status = 'removed'
    else:
        user_favs.append(producto_id)
        status = 'added'

    favoritos[user_id_str] = user_favs
    session['favoritos'] = favoritos

    return jsonify({'status': status})


@cliente.route('/factura/<int:pedido_id>', methods=['GET'])
@login_required
def factura(pedido_id):
    """
    Devuelve los datos de la factura en formato JSON
    """
    try:
        datos = recivo(pedido_id)  # función de basedatos.queries
        return jsonify(datos)
    except Exception as e:
        print("💥 Error al obtener factura:", e)
        return jsonify({"error": str(e)}), 500


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
