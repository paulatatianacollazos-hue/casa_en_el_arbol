from flask import render_template, request, Blueprint, flash
from flask import jsonify, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from basedatos.models import (
    Usuario, Calendario, Notificaciones, RegistroEntrega, db
    )
from basedatos.decoradores import role_required
from basedatos.notificaciones import crear_notificacion
from basedatos.db import get_connection
from basedatos.queries import (
    actualizar_pedido as actualizar_pedido_query,
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
@role_required('empleado')
def dashboard():
    return render_template('empleado/dashboard.html')


@empleado.route("/actualizacion_datos", methods=["GET", "POST"])
@login_required
def actualizacion_datos():
    usuario = current_user
    notificaciones = Notificaciones.query.filter_by(
        ID_Usuario=usuario.ID_Usuario
    ).order_by(Notificaciones.Fecha.desc()).all()

    # 📅 Obtener calendario del usuario
    eventos = Calendario.query.filter_by(ID_Usuario=usuario.ID_Usuario).all()

    # ✅ Si el usuario actualiza sus datos
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
        "empleado/actualizacion_datos.html",
        usuario=usuario,
        notificaciones=notificaciones,
        eventos=eventos
    )


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
            p.ID_Pedido, p.FechaPedido, p.Destino,
            u.Nombre AS ClienteNombre, u.Apellido AS ClienteApellido,
            u.Correo AS ClienteCorreo,
            dp.Cantidad, dp.PrecioUnidad, pr.NombreProducto
        FROM pedido p
        INNER JOIN usuario u ON u.ID_Usuario = p.ID_Usuario
        INNER JOIN detalle_pedido dp ON dp.ID_Pedido = p.ID_Pedido
        INNER JOIN producto pr ON pr.ID_Producto = dp.ID_Producto
        WHERE p.ID_Pedido = %s
    """, (pedido_id,))

    pedido = cursor.fetchall()
    cursor.close()
    conn.close()

    if not pedido:
        return jsonify({"error": "Pedido no encontrado"}), 404

    return jsonify(pedido)


@empleado.route("/registro_entrega/<int:pedido_id>", methods=["GET", "POST"])
@login_required
def registro_entrega(pedido_id):
    if request.method == "GET":
        # Mostrar el formulario HTML
        return render_template("empleado/registro_entrega.html",
                               pedido_id=pedido_id)

    # Si es POST → guardar el registro
    try:
        comentario = request.form.get("comentario", "")
        fotos = request.files.getlist("fotos")

        rutas_fotos = []
        for foto in fotos:
            if foto and foto.filename:
                nombre_seguro = secure_filename(f"{pedido_id}_{foto.filename}")
                ruta_guardado = os.path.join(UPLOAD_FOLDER_ENTREGAS,
                                             nombre_seguro)
                os.makedirs(UPLOAD_FOLDER_ENTREGAS, exist_ok=True)
                foto.save(ruta_guardado)
                rutas_fotos.append(f"/{ruta_guardado}")

        # Ejemplo: guardar en tabla RegistroEntrega
        registro = RegistroEntrega(
            ID_Pedido=pedido_id,
            ID_Empleado=current_user.ID_Usuario,
            Comentario=comentario,
            Fotos=",".join(rutas_fotos)
        )
        db.session.add(registro)
        db.session.commit()

        return redirect(url_for("empleado.exito_entrega", pedido_id=pedido_id))

    except Exception as e:
        print("❌ Error registrando entrega:", e)
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@empleado.route("/registro_entrega/exito/<int:pedido_id>")
@login_required
def exito_entrega(pedido_id):
    return render_template("empleado/exito_entrega.html", pedido_id=pedido_id)
