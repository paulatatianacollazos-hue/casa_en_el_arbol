from flask import Blueprint, render_template, request, redirect, url_for
from flask import flash, jsonify, abort
from flask_login import login_required, current_user
from routes.cliente.routes import mensajes
from sqlalchemy import func
from basedatos.models import (
    db, Usuario, Notificaciones,
    Direccion, Calendario, Pedido, Reseñas, Producto
    )
from sqlalchemy import text
import traceback
from werkzeug.security import generate_password_hash
from basedatos.decoradores import role_required
from basedatos.notificaciones import crear_notificacion
from datetime import datetime  # Ajusta según tu modelo
from flask import make_response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from basedatos.queries import (
    obtener_todos_los_pedidos,
    obtener_empleados,
    todos_los_pedidos,
    obtener_comentarios_agrupados,
    buscar_pedidos,
    asignar_empleado as asignar_empleado_query,
    actualizar_pedido as actualizar_pedido_query,
    get_producto_by_id,
    guardar_producto,
    get_productos, detalle, recivo,
    generar_estadisticas_reseñas
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

        flash(f"✅ Rol de {usuario.Nombre} actualizado a {nuevo_rol}",
              "success")
        return redirect(url_for("admin.gestion_roles"))

    usuarios = Usuario.query.all()
    roles_disponibles = ["admin", "cliente", "empleado",]
    return render_template("administrador/gestion_roles.html",
                           usuarios=usuarios, roles=roles_disponibles)


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

    return render_template("administrador/notificaciones_admin.html",
                           notificaciones=notificaciones)


# ---------- CONTROL_PEDIDOS ----------
@admin.route("/control_pedidos", methods=["GET", "POST"])
@login_required
@role_required("admin")
def control_pedidos():
    # Inicializar variables
    pedidos = todos_los_pedidos()
    comentarios = obtener_comentarios_agrupados()
    reportes = []

    # Manejo de filtros según POST
    if request.method == "POST":
        accion = request.form.get("accion")

        if accion == "estado":  # filtro por estado de pedido
            pedido_id = request.form.get("pedido_id")
            return redirect(url_for("admin.control_pedidos", pedido_id=pedido_id))

        elif accion == "reporte":  # búsqueda de reportes
            reportes = buscar_pedidos()

        # Podrías agregar más acciones según necesidad
    resultados = []
    # Renderizar el template unificado con todas las secciones
    return render_template(
        "administrador/control_pedidos.html",
        pedidos=pedidos,
        comentarios=comentarios,
        reportes=reportes,
        resultados=resultados
    )


@admin.route("/control_pedidos/buscar", methods=["POST"])
@login_required
@role_required("admin")
def buscar_reportes_route():
    resultados = buscar_pedidos()  # Esta función ya existe según tu código
    return jsonify({"resultados": resultados})


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


# ---------- ASIGNAR_CALENDARIO ----------
@admin.route("/asignar_calendario", methods=["POST"])
@login_required
@role_required("admin")
def asignar_calendario_route():
    """
    Asigna un empleado a los pedidos seleccionados y programa un evento
    en la tabla Calendario.
    Validaciones:
      - Pedidos no deben tener empleado asignado
      - Empleado no debe tener otro evento en la misma fecha/hora
    """
    data = request.get_json()

    empleado_id = data.get("empleadoId")
    pedidos_ids = data.get("pedidos", [])
    fecha = data.get("fecha")
    hora = data.get("hora")
    ubicacion = data.get("ubicacion", "")
    tipo = data.get("tipo", "Entrega")  # Puedes cambiar el valor por defecto

    # Validación de datos completos
    if not empleado_id or not pedidos_ids or not fecha or not hora:
        return jsonify({"success": False, "message": "Datos incompletos"}), 400

    # Validar que los pedidos seleccionados no tengan empleado asignado
    pedidos_con_empleado = (
        db.session.query(Pedido)
        .filter(Pedido.ID_Pedido.in_(pedidos_ids))
        .filter(Pedido.ID_Empleado.isnot(None))
        .all()
    )

    if pedidos_con_empleado:
        nombres = [f"#{p.ID_Pedido}" for p in pedidos_con_empleado]
        return jsonify({
            "success": False,
            "message": f"No se puede asignar. Los pedidos {', '.join(
                nombres)} ya tienen un empleado asignado."
        }), 400

    # Validar formato de fecha y hora
    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
        hora_dt = datetime.strptime(hora, "%H:%M").time()
    except ValueError:
        return jsonify({"success": False, "message":
                        "Formato de fecha u hora inválido"}), 400

    # Validar que el empleado no tenga otro evento en la misma fecha/hora
    evento_existente = (
        db.session.query(Calendario)
        .filter_by(ID_Usuario=empleado_id, Fecha=fecha_dt, Hora=hora_dt)
        .first()
    )

    if evento_existente:
        return jsonify({"success": False, "message":
                        "El empleado ya tiene un evento en esa fecha y hora"}
                       ), 400

    # Asignar empleado y crear registros en Calendario
    try:
        for pedido_id in pedidos_ids:
            pedido = Pedido.query.get(pedido_id)
            if not pedido:
                continue  # evitar errores si algún ID no existe
            pedido.ID_Empleado = empleado_id

            calendario = Calendario(
                ID_Usuario=empleado_id,
                ID_Pedido=pedido_id,
                Fecha=fecha_dt,
                Hora=hora_dt,
                Ubicacion=ubicacion,
                Tipo=tipo
            )
            db.session.add(calendario)

        db.session.commit()
        return jsonify({"success": True, "message":
                        "Pedidos asignados correctamente"})

    except Exception as e:
        db.session.rollback()
        print("❌ Error en asignar_calendario_route:", e)
        return jsonify({"success": False, "message":
                        "Ocurrió un error al asignar los pedidos"}), 500


# ---------- ESTADISTICAS ----------
@admin.route("/estadisticas")
@login_required
@role_required("admin")
def estadisticas():
    return render_template("administrador/estadisticas_reseñas.html")


@admin.route("/estadisticas_reseñas")
@login_required
@role_required("admin")
def estadisticas_reseñas():
    try:
        print("📊 Generando estadísticas de reseñas...")

        # Total de reseñas
        total = db.session.query(Reseñas).count()

        if total == 0:
            return jsonify({
                "promedio_general": 0,
                "total": 0,
                "por_estrellas": [0, 0, 0, 0, 0],
                "por_mes": [],
                "por_tipo": {"producto": 0, "pedido": 0},
                "negativos": []
            })

        # Promedio general
        promedio = db.session.query(func.avg(Reseñas.Estrellas)).scalar() or 0

        # Conteo por estrellas
        por_estrellas = [
            db.session.query(Reseñas)
            .filter(Reseñas.Estrellas == i)
            .count()
            for i in range(1, 6)
        ]

        # 🔥 PROMEDIO POR MES (PARA MYSQL)
        mensual = db.session.query(
            func.date_format(Reseñas.Fecha, "%Y-%m").label("mes"),
            func.avg(Reseñas.Estrellas).label("prom")
        ).group_by("mes").order_by("mes").all()

        por_mes = [
            {"mes": m.mes, "promedio": float(m.prom)} for m in mensual
        ]

        # 🔥 POR TIPO (CORREGIDO)
        por_tipo = {
            "producto": db.session.query(Reseñas).filter(Reseñas.tipo == "producto").count(),
            "pedido": db.session.query(Reseñas).filter(Reseñas.tipo == "pedido").count()
        }

        # 🔥 RESEÑAS NEGATIVAS
        negativos_query = db.session.query(Reseñas).filter(
            Reseñas.Estrellas <= 2
        ).all()

        negativos = [
            {
                "pedido": r.ID_Referencia,    # ← Ajusta si este nombre es distinto
                "comentario": r.Comentario or "Sin comentario"
            }
            for r in negativos_query
        ]

        return jsonify({
            "promedio_general": round(float(promedio), 2),
            "total": total,
            "por_estrellas": por_estrellas,
            "por_mes": por_mes,
            "por_tipo": por_tipo,
            "negativos": negativos
        })

    except Exception as e:
        print("❌ ERROR EN ESTADÍSTICAS:", e)
        traceback.print_exc()
        return jsonify({"error": "Error interno"}), 500


# ---------- Perfil y Direcciones ----------
@admin.route("/actualizacion_datos", methods=["GET", "POST"])
@login_required
@role_required("admin")
def actualizacion_datos():
    usuario = current_user

    # 🔹 Direcciones del usuario admin
    direcciones = Direccion.query.filter_by(
        ID_Usuario=usuario.ID_Usuario).all()

    # 🔹 Notificaciones del usuario admin
    notificaciones = Notificaciones.query.filter_by(
        ID_Usuario=usuario.ID_Usuario
    ).order_by(Notificaciones.Fecha.desc()).all()

    # 🔹 Calendario: cargar todas las actividades (propias o generales)
    calendario = Calendario.query.order_by(Calendario.Fecha.asc()).all()

    # 🔹 Actualización de perfil
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

    # 🔹 Renderizar plantilla unificada
    return render_template(
        "administrador/admin_actualizacion_datos.html",
        usuario=usuario,
        direcciones=direcciones,
        notificaciones=notificaciones,
        calendario=calendario,
        pedidos=obtener_todos_los_pedidos(),
        empleados=obtener_empleados(),
    )


@admin.route('/envios')
def envios():
    pedidos = obtener_todos_los_pedidos()
    detalles = detalle()
    empleados = obtener_empleados()
    return render_template('envios.html', pedidos=pedidos, detalles=detalles,
                           empleados=empleados)

@admin.route("/direccion/agregar", methods=["POST"])
@login_required
@role_required("admin")
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

    return redirect(url_for("admin_actualizacion_datos"))


@admin.route("/direccion/borrar/<int:id_direccion>", methods=["POST"])
@login_required
@role_required("admin")
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
@role_required("admin")
def catalogo():
    productos = get_productos()
    return render_template("administrador/catalogo.html", productos=productos)


@admin.route('/guardar_producto', methods=['POST'])
@login_required
@role_required("admin")
def guardar_producto_route():
    try:
        producto_id = guardar_producto(
            request.form, request.files.getlist('imagenes[]'))
        return jsonify({"success": True, "message":
                        "Producto guardado con éxito", "id": producto_id})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@admin.route("/producto/<int:id_producto>")
@login_required
@role_required("admin")
def detalle_producto(id_producto):
    producto = get_producto_by_id(id_producto)
    if not producto:
        flash("Producto no encontrado", "error")
        return redirect(url_for("admin.catalogo"))
    return render_template("administrador/admin_detalle.html",
                           producto=producto)


@admin.route("/calendario/pedidos/<fecha>")
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


@admin.route("/calendario/detalles/<fecha>")
@login_required
def detalles_pedidos_por_dia(fecha):
    try:
        # Obtiene todos los eventos (entregas o instalaciones) del día
        eventos = (
            Calendario.query
            .filter_by(ID_Usuario=current_user.ID_Usuario, Fecha=fecha)
            .filter(Calendario.Tipo.in_(["Entrega", "Instalacion"]))
            .all()
        )

        if not eventos:
            return jsonify([])

        resultado = []
        for evento in eventos:
            pedido = Pedido.query.get(evento.ID_Pedido)
            if not pedido:
                continue

            # Se obtienen detalles desde tu función 'detalle()' o 'recivo()'
            detalles_pedido = recivo(pedido.ID_Pedido)

            monto_total = sum(float(item.get("Monto", 0)
                                    ) for item in detalles_pedido)

            resultado.append({
                "ID_Pedido": pedido.ID_Pedido,
                "Ubicacion": evento.Ubicacion,
                "Hora": evento.Hora.strftime("%H:%M"),
                "Tipo": evento.Tipo,
                "Detalles": detalles_pedido,
                "MontoTotal": monto_total
            })

        return jsonify(resultado)

    except Exception as e:
        print("❌ Error obteniendo detalles del día:", e)
        return jsonify({"error": str(e)}), 500


@admin.route('/programaciones/<fecha>')
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


@admin.route("/admin/calendario/nuevo_evento", methods=["POST"])
@login_required
def crear_evento_calendario():
    """
    Crea un nuevo evento o reunión.
    Si el evento es 'Global', será visible para todos los empleados.
    Si el evento es 'Personal', solo lo verá el usuario creador.
    Evita registrar eventos que se solapen ±60 minutos en la misma fecha.
    """
    from datetime import datetime, timedelta
    data = request.get_json()

    try:
        # ────────────────────────────────────────────────
        # 📥 Datos recibidos desde el frontend
        # ────────────────────────────────────────────────
        tipo_evento = data.get("Tipo")    # Ej: "Evento", "Reunión interna"
        visibilidad = data.get("Visibilidad")    # "Personal" o "Global"
        fecha = datetime.strptime(data.get("Fecha"), "%Y-%m-%d").date()
        hora = datetime.strptime(data.get("Hora"), "%H:%M").time()
        ubicacion = data.get("Ubicacion")

        if not all([tipo_evento, visibilidad, fecha, hora]):
            return jsonify({
                "ok": False,
                "error": "Faltan datos obligatorios."
            }), 400

        # ────────────────────────────────────────────────
        # ⏱️ Verificar conflictos en la misma fecha ±60 min
        # ────────────────────────────────────────────────
        hora_dt = datetime.combine(fecha, hora)
        intervalo_inicio = hora_dt - timedelta(minutes=60)
        intervalo_fin = hora_dt + timedelta(minutes=60)

        conflicto = (
            db.session.query(Calendario)
            .filter(Calendario.Fecha == fecha)
            .filter(Calendario.Hora >= intervalo_inicio.time())
            .filter(Calendario.Hora <= intervalo_fin.time())
            .first()
        )

        if conflicto:
            return jsonify({
                "ok": False,
                "error": f"""Ya existe un evento cerca de esa hora (
                    {conflicto.Tipo} a las {conflicto.Hora.strftime(
                        '%H:%M')})."""
            }), 400

        # ────────────────────────────────────────────────
        # 🗓️ Crear nuevo evento
        # ────────────────────────────────────────────────
        nuevo_evento = Calendario(
            Fecha=fecha,
            Hora=hora,
            Ubicacion=ubicacion,
            ID_Usuario=current_user.ID_Usuario,  # usuario creador
            Tipo=visibilidad,                    # 'Personal' o 'Global'
            ID_Pedido=None
        )

        db.session.add(nuevo_evento)
        db.session.commit()

        # ────────────────────────────────────────────────
        # ✅ Respuesta
        # ────────────────────────────────────────────────
        return jsonify({
            "ok": True,
            "mensaje": f"{tipo_evento} creado exitosamente como '{
                visibilidad}'."
        })

    except Exception as e:
        print("❌ Error al crear evento:", e)
        db.session.rollback()
        return jsonify({
            "ok": False,
            "error": "Error interno al crear el evento."
        }), 500


@admin.route('/factura/pdf/<int:pedido_id>', methods=['GET'])
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


@admin.route("/admin/empleados_calendario")
@login_required
def empleados_calendario():
    if current_user.Rol != "admin":
        return jsonify({"error": "No autorizado"}), 403

    empleados = (
        db.session.query(Usuario.ID_Usuario, Usuario.Nombre, Usuario.Apellido)
        .filter(Usuario.Rol == "empleado")
        .all()
    )

    data = [
        {"id": e.ID_Usuario, "nombre": f"{e.Nombre} {e.Apellido}"}
        for e in empleados
    ]
    return jsonify(data)


@admin.route('/factura/<int:pedido_id>', methods=['GET'])
@login_required
def factura_json(pedido_id):
    """
    Devuelve los datos de la factura en formato JSON
    para que puedan mostrarse en el modal de la interfaz.
    """
    try:
        datos = recivo(pedido_id)

        # Validar que la función recivo() devuelva una lista
        if not datos:
            return jsonify({"error":
                            "No se encontraron datos para esta factura"}), 404

        return jsonify(datos)

    except Exception as e:
        print("❌ Error en factura_json:", e)
        return jsonify({"error": str(e)}), 500


@admin.route('/registros_entrega/<int:pedido_id>', methods=['GET'])
@login_required
def registros_entrega_json(pedido_id):
    try:
        registros = db.session.execute(text("""
            SELECT
                ID_Registro,
                ID_Pedido,
                ID_Empleado,
                Comentario,
                FechaRegistro,
                Foto1,
                Foto2,
                Foto3
            FROM registros_entrega
            WHERE ID_Pedido = :pedido_id
        """), {'pedido_id': pedido_id}).mappings().all()

        if not registros:
            return jsonify({
                "success": False,
                "message": f"No se encontraron registros de entrega para el pedido #{pedido_id}.",
                "registros": [],
                "fotos": []
            }), 200

        lista_registros = []
        lista_fotos = []

        for r in registros:
            lista_registros.append({
                "id_registro": r["ID_Registro"],
                "empleado": r["ID_Empleado"],
                "comentario": r["Comentario"],
                "fecha": str(r["FechaRegistro"])
            })

            # === Procesar fotos ===
            for campo_foto in ["Foto1", "Foto2", "Foto3"]:
                foto = r.get(campo_foto)
                if foto:
                    lista_fotos.append(f"/static/img/entregas/{foto}")

        return jsonify({
            "success": True,
            "registros": lista_registros,
            "fotos": lista_fotos
        }), 200

    except Exception as e:
        print("❌ Error obteniendo registros_entrega:")
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Ocurrió un error al obtener los registros de entrega."
        }), 500


# ------------------ CHAT ADMIN ------------------
# importa la lista global de mensajes del cliente
@admin.route('/chat')
@login_required
def chat_admin():
    return render_template('common/chat.html', usuario='Administrador')


@admin.route('/enviar_mensaje', methods=['POST'])
@login_required
def enviar_mensaje_admin():
    data = request.get_json()
    mensajes.append({
        'usuario': 'Administrador',
        'texto': data.get('texto'),
        'fecha': datetime.now().isoformat()
    })
    return jsonify({'ok': True})


@admin.route('/obtener_mensajes')
@login_required
def obtener_mensajes_admin():
    return jsonify(mensajes)


@admin.route("/usuarios_calendario")
@login_required
@role_required("admin")
def usuarios_calendario():
    try:
        usuarios = db.session.query(Usuario).all()

        data = []
        for u in usuarios:
            id_usuario = (
                getattr(u, "ID_Usuario", None) or
                getattr(u, "ID_usuario", None) or
                getattr(u, "id_usuario", None) or
                getattr(u, "id", None)
            )

            data.append({
                "id": id_usuario,
                "nombre": f"{u.Nombre} {u.Apellido}",
                "rol": u.Rol
            })

        return jsonify({"usuarios": data})

    except Exception as e:
        print("❌ Error cargando usuarios:", e)
        return jsonify({"error": "Error interno"}), 500


@admin.route("/empleado/programaciones_todas")
@login_required
def programaciones_todas():
    try:
        eventos = Calendario.query.all()

        data = [e.to_dict() for e in eventos]

        return jsonify({"eventos": data})

    except Exception as e:
        print("❌ Error cargando programaciones:", e)
        return jsonify({"error": "Error interno"}), 500


@admin.route("/buscar", methods=["GET"])
def buscar():
    try:
        q = request.args.get("q", "").strip()

        if not q:
            return jsonify({"productos": [], "pedidos": []})

        productos = Producto.query.filter(
            Producto.NombreProducto.ilike(f"%{q}%")
        ).all()

        pedidos = []
        if q.isdigit():
            pedidos = Pedido.query.filter(
                Pedido.ID_Pedido == int(q)
            ).all()

        return jsonify({
            "productos": [
                {
                    "id": p.ID_Producto,
                    "nombre": p.NombreProducto,
                    "precio": p.PrecioUnidad,
                    "imagen": url_for("static", filename=p.Imagen)
                } for p in productos
            ],
            "pedidos": [
                {
                    "id": ped.ID_Pedido,
                    "estado": ped.Estado,
                    "total": ped.Total,
                    "fecha": ped.Fecha.strftime("%Y-%m-%d")
                } for ped in pedidos
            ]
        })

    except Exception as e:
        print("\n❌ ERROR EN /admin/buscar →", e, "\n")
        return jsonify({"error": str(e)}), 500
