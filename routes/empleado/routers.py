from flask import render_template, request, Blueprint, flash
from flask import jsonify, redirect, url_for, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from basedatos.models import (
    Usuario, Calendario, Notificaciones, RegistroEntrega, db,
    Pedido, Detalle_Pedido, Producto, Reseñas
    )
from basedatos.decoradores import role_required
from basedatos.notificaciones import crear_notificacion
from basedatos.db import get_connection
from basedatos.queries import (
    actualizar_pedido as actualizar_pedido_query,
    get_productos, get_producto_by_id
)
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER_ENTREGAS = "static/uploads/entregas"
os.makedirs(UPLOAD_FOLDER_ENTREGAS, exist_ok=True)

empleado = Blueprint(
    'empleado',
    __name__,
    template_folder='templates',
    url_prefix='/empleado'
)


@empleado.route('/dashboard')
@login_required
@role_required('instalador', 'transportista', 'taller')
def dashboard():
    return render_template('empleado/dashboard.html')


@empleado.route("/actualizacion_datos", methods=["GET", "POST"])
@login_required
def actualizacion_datos():
    usuario = current_user

    # 🔔 Notificaciones
    notificaciones = Notificaciones.query.filter_by(
        ID_Usuario=usuario.ID_Usuario
    ).order_by(Notificaciones.Fecha.desc()).all()

    # 📅 Calendario
    eventos = Calendario.query.filter_by(
        ID_Usuario=usuario.ID_Usuario
    ).all()

    # 📦 Pedidos pendientes (solo taller)
    pedidos = None
    if usuario.Rol == "taller":
        page = request.args.get("page", 1, type=int)

        pedidos = Pedido.query.filter(
            Pedido.Estado == "pendiente"
        ).order_by(
            Pedido.FechaPedido.desc()
        ).paginate(
            page=page,
            per_page=20,   # ✅ 20 pedidos visibles
            error_out=False
        )

    return render_template(
        "empleado/actualizacion_datos.html",
        usuario=usuario,
        notificaciones=notificaciones,
        eventos=eventos,
        pedidos=pedidos
    )


@empleado.route("/pedido/<int:pedido_id>/completar", methods=["POST"])
@login_required
def completar_pedido(pedido_id):
    if current_user.Rol != "taller":
        abort(403)

    pedido = Pedido.query.get_or_404(pedido_id)
    pedido.Estado = "en proceso"
    db.session.commit()

    flash("Pedido cambiado a 'en proceso'", "success")
    return redirect(url_for("empleado.actualizacion_datos"))


@empleado.route("/calendario/pedidos/<fecha>")
@login_required
def pedidos_por_dia(fecha):
    try:
        pedidos = (
            Calendario.query
            .filter_by(ID_Usuario=current_user.id, Fecha=fecha)
            .all()
        )
        if not pedidos:
            return jsonify([])

        resultado = [
            {
                "ID_Pedido": p.ID_Pedido,
                "Ubicacion": p.Ubicacion,
                "Hora": p.Hora.strftime("%H:%M"),
                "Tipo": p.Tipo,
            }
            for p in pedidos
        ]
        return jsonify(resultado)
    except Exception as e:
        print("Error en /calendario/pedidos:", e)
        return jsonify([]), 500


@empleado.route('/programaciones/<fecha>')
@login_required
def obtener_programaciones(fecha):
    try:
        resultados = Calendario.query.filter_by(
            ID_Usuario=current_user.id,
            Fecha=fecha
        ).all()

        return jsonify([
            {
                "ID_Calendario": c.ID_Calendario,
                "ID_Pedido": c.ID_Pedido,
                "Fecha": str(c.Fecha),
                "Hora": str(c.Hora),
                "Ubicacion": c.Ubicacion,
                "Tipo": c.Tipo,
                "Descripcion": getattr(c, "Descripcion", "")
            }
            for c in resultados
        ])
    except Exception as e:
        print("Error:", e)
        return jsonify([]), 500


@empleado.route('/programaciones_todas')
@login_required
def programaciones_todas():
    eventos = Calendario.query.filter_by(ID_Usuario=current_user.ID_Usuario
                                         ).all()
    return jsonify([
        {
            "ID_Calendario": e.ID_Calendario,
            "Fecha": e.Fecha.strftime("%Y-%m-%d"),
            "Hora": str(e.Hora),
            "Ubicacion": e.Ubicacion,
            "ID_Pedido": e.ID_Pedido,
            "Tipo": e.Tipo
        }
        for e in eventos
    ])


@empleado.route("/empleado/programaciones_globales")
@login_required
def programaciones_globales():
    registros = Calendario.query.all()
    data = [
        {
            "ID_Calendario": c.ID_Calendario,
            "Fecha": c.Fecha.strftime("%Y-%m-%d"),
            "Hora": c.Hora.strftime("%H:%M") if c.Hora else None,
            "Ubicacion": c.Ubicacion,
            "Tipo": c.Tipo,
            "Empleado_ID": c.ID_Usuario,
        }
        for c in registros
    ]
    return jsonify(data)


@empleado.route("/empleado/programaciones_todas")
@login_required
def obtener_programaciones_todas():
    """Devuelve todos los eventos visibles para el usuario actual."""
    try:
        eventos = (
            db.session.query(Calendario)
            .filter(
                (Calendario.Tipo == "Global") |
                (Calendario.ID_Usuario == current_user.ID_Usuario)
            )
            .all()
        )

        resultado = [
            {
                "ID_Calendario": ev.ID_Calendario,
                "Fecha": ev.Fecha.strftime("%Y-%m-%d"),
                "Hora": ev.Hora.strftime("%H:%M"),
                "Ubicacion": ev.Ubicacion,
                "Tipo": ev.Tipo,  # Personal o Global
                "Empleado_ID": ev.ID_Usuario,
                "Empleado": f"{ev.usuario.Nombre} {
                    ev.usuario.Apellido}" if hasattr(ev, "usuario") else "N/A",
                "ID_Pedido": ev.ID_Pedido
            }
            for ev in eventos
        ]

        return jsonify(resultado)

    except Exception as e:
        print("❌ Error al obtener programaciones:", e)
        return jsonify({
            "error": "No se pudieron obtener las programaciones"}), 500


@empleado.route("/estado", methods=["GET", "POST"])
@login_required
@role_required("empleado")
def estado_pedido():
    if request.method == "POST":
        pedido_id = request.form["pedido_id"]
        return redirect(url_for("admin.control_pedidos", pedido_id=pedido_id))
    return render_template("empleado/actualizacion_datos.html")


@empleado.route("/actualizar_pedido", methods=["POST"])
@login_required
@role_required("empleado")
def actualizar_pedido_route():
    actualizar_pedido_query(request.form)
    return redirect(url_for("empleado.actualizacion_datos"))


@empleado.route('/detalle_pedido/<int:pedido_id>', methods=['GET'])
@login_required
def detalle_pedido(pedido_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            p.ID_Pedido,
            p.FechaPedido,
            p.Estado,
            u.Nombre AS ClienteNombre,
            u.Apellido AS ClienteApellido,
            dp.ID_Producto,
            dp.Cantidad,
            dp.PrecioUnidad,
            pr.NombreProducto,
            COALESCE(prr.Recogido, 0) AS marcado  -- ✅ marcar si ya fue recogido
        FROM pedido p
        INNER JOIN usuario u ON u.ID_Usuario = p.ID_Usuario
        INNER JOIN detalle_pedido dp ON dp.ID_Pedido = p.ID_Pedido
        INNER JOIN producto pr ON pr.ID_Producto = dp.ID_Producto
        LEFT JOIN productos_recogidos prr
               ON prr.ID_Pedido = p.ID_Pedido AND prr.ID_Producto = dp.ID_Producto
        WHERE p.ID_Pedido = %s
    """, (pedido_id,))

    pedido = cursor.fetchall()
    cursor.close()
    conn.close()

    if not pedido:
        return jsonify({"error": "Pedido no encontrado"}), 404

    return jsonify(pedido)


@empleado.route('/registro_entrega/<int:pedido_id>', methods=['GET', 'POST'])
@login_required
def registro_entrega(pedido_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        comentario = request.form.get('comentario')
        fotos = request.files.getlist('fotos')

        # ✅ Carpeta donde se guardarán las imágenes
        carpeta_destino = os.path.join('static', 'img')
        os.makedirs(carpeta_destino, exist_ok=True)

        fotos_guardadas = []
        for foto in fotos[:3]:  # límite de 3 fotos
            if foto and foto.filename.strip() != '':
                nombre_archivo = secure_filename(foto.filename)
                ruta_completa = os.path.join(carpeta_destino, nombre_archivo)
                foto.save(ruta_completa)
                fotos_guardadas.append(nombre_archivo)
            else:
                fotos_guardadas.append(None)

        # Rellenar con None las fotos faltantes
        while len(fotos_guardadas) < 3:
            fotos_guardadas.append(None)

        # 🔹 Insertar en registros_entrega
        cursor.execute("""
            INSERT INTO registros_entrega (
                ID_Pedido, ID_Empleado, Comentario,
                Foto1, Foto2, Foto3
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            pedido_id,
            current_user.id,
            comentario,
            fotos_guardadas[0],
            fotos_guardadas[1],
            fotos_guardadas[2]
        ))

        # 🔹 Actualizar el estado del pedido
        cursor.execute("""
            UPDATE pedido
            SET Estado = 'entregado'
            WHERE ID_Pedido = %s
        """, (pedido_id,))

        conn.commit()
        cursor.close()
        conn.close()

        flash(
            "✅ Registro de entrega guardado y pedido marcado como entregado.",
            "success")
        return redirect(url_for('empleado.dashboard'))

    # Si es GET, mostrar formulario con datos del pedido
    cursor.execute("""
        SELECT p.*, c.Nombre AS ClienteNombre, c.Apellido AS ClienteApellido
        FROM pedido p
        JOIN usuario c ON p.ID_usuario = c.ID_usuario
        WHERE p.ID_Pedido = %s
    """, (pedido_id,))
    pedido = cursor.fetchone()
    cursor.close()
    conn.close()

    if not pedido:
        flash("❌ Pedido no encontrado.", "danger")
        return redirect(url_for('empleado.dashboard'))

    return render_template("empleado/registro_entrega.html", pedido=pedido)


@empleado.route("/nosotros")
def nosotros():
    return render_template("empleado/Nosotros.html")


@empleado.route("/pedido/<int:id_pedido>/productos", methods=["GET", "POST"])
@login_required
def pedido_productos(id_pedido):
    pedido = Pedido.query.get_or_404(id_pedido)
    productos = (
        db.session.query(Detalle_Pedido, Producto)
        .join(Producto, Detalle_Pedido.ID_Producto == Producto.ID_Producto)
        .filter(Detalle_Pedido.ID_Pedido == id_pedido)
        .all()
    )

    if request.method == "POST":
        # Guardar el estado de los checkboxes
        for detalle, producto in productos:
            marcado = str(producto.ID_Producto) in request.form
            detalle.marcado = marcado  # Suponiendo que agregas un campo "marcado" en Detalle_Pedido
            db.session.add(detalle)
        db.session.commit()
        flash("Estado de productos actualizado", "success")
        return redirect(url_for("cliente.detalle_pedido", id_pedido=id_pedido))

    return render_template("cliente/pedido_productos.html", pedido=pedido, productos=productos)


@empleado.route("/actualizar_productos/<int:pedido_id>", methods=["POST"])
@login_required
def actualizar_productos(pedido_id):
    data = request.json

    seleccionados = data.get("seleccionados", [])
    no_seleccionados = data.get("noSeleccionados", [])

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Guardar productos marcados como recogidos
        for producto_id in seleccionados:
            cursor.execute("""
                INSERT INTO productos_recogidos (ID_Pedido, ID_Producto, Recogido)
                VALUES (%s, %s, 1)
                ON DUPLICATE KEY UPDATE Recogido = 1
            """, (pedido_id, producto_id))

        # Guardar productos NO recogidos
        for producto_id in no_seleccionados:
            cursor.execute("""
                INSERT INTO productos_recogidos (ID_Pedido, ID_Producto, Recogido)
                VALUES (%s, %s, 0)
                ON DUPLICATE KEY UPDATE Recogido = 0
            """, (pedido_id, producto_id))

        conn.commit()
        return jsonify({"success": True})

    except Exception as e:
        conn.rollback()
        print("❌ Error en actualizar_productos:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@empleado.route("/catalogo")
@login_required
def catalogo():
    productos = get_productos()
    return render_template("empleado/catalogo.html",
                           productos=productos)


@empleado.route("/producto/<int:id_producto>")
@login_required
def detalle_producto(id_producto):
    producto = get_producto_by_id(id_producto)
    if not producto:
        flash("Producto no encontrado", "error")
        return redirect(url_for("empleado.catalogo"))

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
        "empleado/empleado_detalle.html",
        producto=producto,
        ha_comprado=ha_comprado,
        reseñas=reseñas
    )


@empleado.route("/producto/<int:id>/defectuoso", methods=["POST"])
@login_required
def marcar_defectuoso(id):
    producto = Producto.query.get_or_404(id)
    data = request.get_json()  # <-- recibir JSON
    descripcion = data.get("descripcion", "")

    if producto.Stock > 0:
        producto.Stock -= 1
        db.session.commit()
        # aquí podrías guardar la descripción en otra tabla si quieres
        return {"success": True}
    
    return {"success": False, "error": "Stock insuficiente"}, 400
