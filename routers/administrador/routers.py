from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta

from basedatos.models import db, Usuario, Notificaciones
from basedatos.decoradores import role_required, crear_notificacion, obtener_todos_los_pedidos, detalle,obtener_empleados, todos_los_pedidos, get_connection, obtener_comentarios_agrupados, obtener_productos, obtener_producto_por_id

reviews = []

admin = Blueprint('admin', __name__, url_prefix='/admin')  

# ---------- DASHBOARDS ----------
@admin.route('/admin')
@login_required
@role_required('admin')
def admin_dashboard():
    return render_template('administrador/admin_dashboard.html')


# ---------- GESTION_ROLES ----------
@admin.route('/gestion_roles', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def gestion_roles():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        nuevo_rol = request.form.get('rol')

        usuario = Usuario.query.get(user_id)
        if not usuario:
            flash("❌ Usuario no encontrado", "danger")
            return redirect(url_for('roles.gestion_roles'))  

        usuario.Rol = nuevo_rol
        db.session.commit()

        flash(f"✅ Rol de {usuario.Nombre} actualizado a {nuevo_rol}", "success")
        return redirect(url_for('roles.gestion_roles')) 

    usuarios = Usuario.query.all()
    roles_disponibles = ["admin", "cliente", "instalador", "transportista"]
    return render_template("administrador/gestion_roles.html", usuarios=usuarios, roles=roles_disponibles)

# ---------- CAMBIAR_ROL----------

@admin.route('/cambiar_rol/<int:user_id>', methods=['POST'])
@login_required
def cambiar_rol(user_id):
    nuevo_rol = request.form['rol']
    usuario = Usuario.query.get(user_id)  
    
    if usuario:
        usuario.Rol = nuevo_rol  
        db.session.commit()      
        flash(f"✅ Rol de {usuario.Nombre} cambiado a {nuevo_rol}", "success")
    else:
        flash("❌ Usuario no encontrado", "danger")
    
    return redirect(url_for('gestion_roles'))

# ---------- RESEÑAS----------
@admin.route('/admin')
@login_required
def admin():
    
    return render_template("administrador/admin_reseñas.html", reviews=reviews)

# ---------- NOTIFICACIONES_ADMIN ----------
@admin.route('/admin', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def ver_notificaciones_admin():
    if request.method == 'POST':
        ids = request.form.getlist('ids')
        if not ids:
            flash("❌ No seleccionaste ninguna notificación", "warning")
            return redirect(url_for('notificaciones.ver_notificaciones_admin'))

        try:
            ids_int = [int(i) for i in ids if str(i).isdigit()]
        except ValueError:
            flash("❌ IDs inválidos", "danger")
            return redirect(url_for('notificaciones.ver_notificaciones_admin'))

        try:
            Notificaciones.query.filter(
                Notificaciones.ID_Usuario == current_user.ID_Usuario,
                Notificaciones.ID_Notificacion.in_(ids_int)
            ).delete(synchronize_session=False)
            db.session.commit()
            flash("✅ Notificaciones eliminadas", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error al eliminar: {e}", "danger")

        return redirect(url_for('notificaciones.ver_notificaciones_admin'))

    notificaciones = Notificaciones.query.filter_by(
        ID_Usuario=current_user.ID_Usuario
    ).order_by(Notificaciones.Fecha.desc()).all()

    return render_template("administrador/notificaciones_admin.html", notificaciones=notificaciones)

# ---------- ENVIOS ----------

@admin.route('/envios')
@login_required
@role_required('admin')
def envios():
    pedidos = obtener_todos_los_pedidos()
    detalles = detalle()
    empleados = obtener_empleados()
    return render_template('administrador/envios.html', pedidos=pedidos, detalles=detalles,
                           empleados=empleados)

# ----------+CONTROL_PEDIDOS ----------

@admin.route("/control_pedidos")
@login_required
@role_required('admin')
def control_pedidos():
    pedidos = todos_los_pedidos()
    return render_template('administrador/control_pedidos.html', pedidos=pedidos)


# ---------- ASIGNAR_EMPLEADO----------

@admin.route('/asignar_empleado', methods=['POST'])
def asignar_empleado():
    pedido_ids = request.form['pedido_id'].split(",")
    empleado_id = request.form['empleado_id']

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    mensajes = []
    for pid in pedido_ids:
        # 1️⃣ obtener hora del pedido que quiero asignar
        cursor.execute("""
            SELECT HoraEntrega
            FROM Pedido
            WHERE ID_Pedido = %s
        """, (pid,))
        pedido = cursor.fetchone()

        if not pedido or not pedido['HoraEntrega']:
            mensajes.append(f"❌ Pedido {pid} no tiene hora definida")
            continue

        hora_pedido = pedido['HoraEntrega']


        cursor.execute("""
            SELECT ID_Pedido, HoraEntrega
            FROM Pedido
            WHERE ID_Empleado = %s
            AND ABS(TIMESTAMPDIFF(MINUTE, HoraEntrega, %s)) < 30
        """, (empleado_id, hora_pedido))
        conflicto = cursor.fetchone()

        if conflicto:
            mensajes.append(f"""❌ Pedido {pid} no se asignó.
                            Conflicto con pedido {conflicto['ID_Pedido']}
                            en el calendario.""")
            continue

        # 3️⃣ asignar si no hay conflicto
        cursor.execute("""
            UPDATE Pedido
            SET ID_Empleado = %s
            WHERE ID_Pedido = %s
        """, (empleado_id, pid))
        mensajes.append(f"✅ Pedido {pid} asignado correctamente")

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"success": True, "message": "<br>".join(mensajes)})

# ---------- ACTUALIZAR_PEDIDO ----------

@admin.route('/actualizar_pedido', methods=['POST'])
def actualizar_pedido():
    pedido_id = request.form['pedido_id']
    nuevo_estado = request.form['estado']
    comentario = request.form['comentario']

    conn = get_connection() 
    cursor = conn.cursor()

    try:
       
        cursor.execute("""
            UPDATE Pedido
            SET Estado = %s
            WHERE ID_Pedido = %s
        """, (nuevo_estado, pedido_id))

      
        if comentario.strip():
            cursor.execute("""
                INSERT INTO comentarios (pedido_id, texto)
                VALUES (%s, %s)
            """, (pedido_id, comentario))

        conn.commit()
        flash("Pedido actualizado correctamente", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al actualizar el pedido: {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('control_pedidos')) 

# ---------- ESTADO----------

@admin.route('/estado', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def buscar_pedido():
    if request.method == 'POST':
        pedido_id = request.form['pedido_id']
        return redirect(url_for('administrador/control_pedidos.html', pedido_id=pedido_id))
    return render_template('administrador/estado.html')

# ---------- COMENTARIOS ----------

@admin.route('/comentarios')
@login_required
@role_required('admin')
def mostrar_comentarios():
    comentarios = obtener_comentarios_agrupados()
    return render_template('administrador/comentarios.html', comentarios=comentarios)

# ---------- PRODUCTOS----------
@admin.route('/productos')
def listar_productos():
    productos = obtener_productos()
    return render_template('productos.html', productos=productos)

@admin.route('/producto/<int:producto_id>')
def ver_producto(producto_id):
    producto = obtener_producto_por_id(producto_id)
    if not producto:
        return "Producto no encontrado", 404
    return render_template('detalles.html', producto=producto)


# ---------- REPORTE----------

@admin.route('/reporte', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def buscar_pedidos():
    resultados = []

    if request.method == 'POST':
        fecha = request.form.get('fecha_pedido')
        id_pedido = request.form.get('id_pedido')
        nombre_cliente = request.form.get('nombre_cliente')
        nombre_empleado = request.form.get('nombre_empleado')

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT
                p.ID_Pedido AS id_pedido,
                p.FechaPedido AS fecha,
                c.Nombre AS cliente,
                c.Direccion AS direccion,
                GROUP_CONCAT(CONCAT(pr.NombreProducto, ' x', dp.Cantidad)
                SEPARATOR '<br>') AS productos,
                p.Estado AS estado,
                COALESCE(e.Nombre, 'Sin asignar') AS empleado
            FROM Pedido p
            JOIN Usuario c ON p.ID_Usuario = c.ID_Usuario
            JOIN Detalle_Pedido dp ON p.ID_Pedido = dp.ID_Pedido
            JOIN Producto pr ON dp.ID_Producto = pr.ID_Producto
            LEFT JOIN Usuario e ON p.ID_Empleado = e.ID_Usuario
            WHERE p.Estado = 'entregado'
        """
        params = []

        if fecha:
            query += " AND p.FechaPedido = %s"
            params.append(fecha)

        if id_pedido:
            query += " AND p.ID_Pedido = %s"
            params.append(id_pedido)

        if nombre_cliente:
            query += " AND c.Nombre LIKE %s"
            params.append(f"%{nombre_cliente}%")

        if nombre_empleado:
            query += " AND e.Nombre LIKE %s"
            params.append(f"%{nombre_empleado}%")

        # 👇 agrupar y ordenar SOLO al final
        query += """
            GROUP BY p.ID_Pedido, p.FechaPedido, c.Nombre, c.Direccion,
            p.Estado, e.Nombre
            ORDER BY p.FechaPedido DESC
        """

        cursor.execute(query, tuple(params))
        resultados = cursor.fetchall()
        cursor.close()
        conn.close()

    return render_template('administrador/reportes_entrega.html', resultados=resultados)


# ---------- ASIGNAR_CALENDARIO----------


@admin.route("/asignar_calendario", methods=["POST"])
def asignar_calendario():
    print("📩 Datos recibidos:", request.form.to_dict())
    pedidos_ids = request.form.get("pedidosSeleccionados").split(",")
    empleado_id = request.form["empleado_id"]
    fecha = request.form["fecha"]
    hora_inicio = request.form["hora"]

    # Convertir fecha y hora a datetime inicial
    start_datetime = datetime.strptime(f"{fecha} {hora_inicio}",
                                       "%Y-%m-%d %H:%M")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        for pedido_id in pedidos_ids:
            # Ver si el pedido es instalación
            cursor.execute("SELECT Instalacion FROM Pedido WHERE ID_Pedido = %s", (pedido_id,))
            instalacion = cursor.fetchone()[0]

            intervalo = timedelta(minutes=60) if instalacion == "si" else timedelta(minutes=30)

            # 🔹 Validar si ya existe una cita en ese día, hora y empleado
            cursor.execute("""
                SELECT COUNT(*)
                FROM Calendario
                WHERE Fecha = %s AND Hora = %s AND ID_Usuario = %s
            """, (fecha, start_datetime.strftime("%H:%M:%S"), empleado_id))

            existe = cursor.fetchone()[0]

            if existe > 0:
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({
                    "success": False,
                    "message": f"⚠️ El empleado ya tiene una cita el {fecha} a las {start_datetime.strftime('%H:%M')}."
                })

            # 🟢 Guardamos en la tabla Pedido
            cursor.execute("""
                UPDATE Pedido
                SET ID_Empleado = %s,
                    FechaEntrega = %s,
                    HoraEntrega = %s
                WHERE ID_Pedido = %s
            """, (empleado_id, fecha, start_datetime.strftime("%H:%M:%S"), pedido_id))

            # 🟢 Insertar también en la tabla Calendario
            cursor.execute("""
                INSERT INTO Calendario (Fecha, Hora, Ubicacion, ID_Usuario, ID_Pedido, Tipo)
                SELECT %s, %s, u.Direccion, %s, p.ID_Pedido, p.Instalacion
                FROM Pedido p
                JOIN Usuario u ON p.ID_Usuario = u.ID_Usuario
                WHERE p.ID_Pedido = %s
            """, (fecha, start_datetime.strftime("%H:%M:%S"), empleado_id, pedido_id))

            # Avanzar a la siguiente hora según instalación o normal
            start_datetime += intervalo

        conn.commit()
        return jsonify({
            "success": True,
            "message": "✅ Pedidos asignados y calendario actualizado"
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": f"❌ Error: {str(e)}"})

    finally:
        cursor.close()
        conn.close()




