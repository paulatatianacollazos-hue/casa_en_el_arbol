from flask import request, jsonify
from sqlalchemy import func
from datetime import datetime, timedelta
from basedatos.db import get_connection
from sqlalchemy import and_
from basedatos.models import (
    db, Pedido, Usuario, Detalle_Pedido, Comentarios, Reseñas)
from basedatos.models import Producto, Calendario
import os
from werkzeug.utils import secure_filename
from flask import current_app
from collections import defaultdict
from flask import url_for
from flask_mail import Message
from decoradores import mail


UPLOAD_FOLDER = os.path.join("static", "img")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------OBTENER_PEDIDOS ---------
def obtener_todos_los_pedidos():
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            pe.ID_Pedido,            -- 0
            u.Nombre AS nombre_usuario, -- 1
            u.Telefono,              -- 2
            u.Direccion,             -- 3
            p.ID_Producto,           -- 4
            p.NombreProducto,        -- 5
            dp.Cantidad,             -- 6
            pe.FechaPedido,          -- 7
            ip.ruta AS ImagenURL,    -- 8
            p.PrecioUnidad,          -- 9
            pe.ID_Empleado,          -- 10
            pe.Instalacion,          -- 11
            pe.Estado                -- 🔹 12 (NUEVO)
        FROM Pedido pe
        JOIN Usuario u ON pe.ID_Usuario = u.ID_Usuario
        JOIN Detalle_Pedido dp ON pe.ID_Pedido = dp.ID_Pedido
        JOIN Producto p ON dp.ID_Producto = p.ID_Producto
        LEFT JOIN ImagenProducto ip ON p.ID_Producto = ip.ID_Producto
        ORDER BY pe.FechaPedido DESC;
    """

    cursor.execute(query)
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()

    pedidos_dict = {}

    for row in resultados:
        id_pedido = row[0]
        id_producto = row[4]

        # 🔹 Limpiar ruta de imagen
        imagen_ruta = row[8] or ''
        if imagen_ruta:
            imagen_ruta = os.path.basename(imagen_ruta)

        producto = {
            'id': id_producto,
            'nombre': row[5],
            'cantidad': row[6],
            'imagen': imagen_ruta,
            'precio': float(row[9])
        }

        fecha = row[7].strftime('%Y-%m-%d')

        if id_pedido not in pedidos_dict:
            pedidos_dict[id_pedido] = {
                'id': id_pedido,
                'usuario': row[1],
                'telefono': row[2],
                'direccion': row[3],
                'fecha': fecha,
                'productos': {},
                'id_empleado': row[10],
                'instalacion': row[11],
                'estado': row[12]  # 🔹 AQUÍ SE GUARDA ESTADO
            }

        productos = pedidos_dict[id_pedido]['productos']

        if id_producto in productos:
            productos[id_producto]['cantidad'] += producto['cantidad']
        else:
            productos[id_producto] = producto

    # 🔹 Calcular totales
    for pedido in pedidos_dict.values():
        pedido['productos'] = list(pedido['productos'].values())
        pedido['total'] = round(
            sum(prod['cantidad'] * prod['precio'] for prod in pedido['productos']),
            2
        )

    return list(pedidos_dict.values())

# --------- TODOS_LOS_PEDIDOS ---------


def todos_los_pedidos():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
       SELECT
            pe.ID_Pedido,
            MAX(pe.FechaPedido) AS FechaPedido,
            MAX(pe.FechaEntrega) AS FechaEntrega,
            MAX(u.Nombre) AS cliente,
            MAX(u.Direccion) AS direccion,
            GROUP_CONCAT(CONCAT(pr.NombreProducto, ' x', dp.Cantidad)
            SEPARATOR '<br>') AS productos,
            MAX(pe.Estado) AS Estado,
            MAX(emp.Nombre) AS empleado
        FROM Pedido pe
        JOIN Usuario u ON pe.ID_Usuario = u.ID_Usuario
        LEFT JOIN Detalle_Pedido dp ON pe.ID_Pedido = dp.ID_Pedido
        LEFT JOIN Producto pr ON dp.ID_Producto = pr.ID_Producto
        LEFT JOIN Usuario emp ON pe.ID_Empleado = emp.ID_Usuario
        GROUP BY pe.ID_Pedido
        ORDER BY pe.ID_Pedido DESC;

    """)
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados


def detalle():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            p.ID_Pedido,
            u.Nombre AS Nombre_Cliente,
            u.Telefono,
            u.Direccion,
            pr.NombreProducto AS Producto,
            im.ruta AS ruta,
            dp.Cantidad
        FROM Pedido p
        JOIN Usuario u ON p.ID_Usuario = u.ID_Usuario
        JOIN Detalle_Pedido dp ON p.ID_Pedido = dp.ID_Pedido
        JOIN Producto pr ON dp.ID_Producto = pr.ID_Producto
        join imagenproducto im on im.ID_Producto = pr.ID_Producto
    """)
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()

    agrupado = {}
    for row in resultados:
        pid = str(row['ID_Pedido'])  # <-- convertir a string
        if pid not in agrupado:
            agrupado[pid] = {
                'Nombre_Cliente': row['Nombre_Cliente'],
                'Telefono': row['Telefono'],
                'Direccion': row['Direccion'],
                'Productos': []
            }
        agrupado[pid]['Productos'].append({
            'Producto': row['Producto'],
            'Cantidad': row['Cantidad'],
            'ruta': row['ruta']
        })

    return agrupado

# --------- OBTENER_EMPLEADOS ---------


def obtener_empleados():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
    SELECT ID_Usuario AS ID_Empleado, Nombre
    FROM Usuario
    WHERE Rol = 'Empleado'
    """)
    empleados = cursor.fetchall()
    cursor.close()
    conn.close()
    return empleados


# --------- OBTENER_PRODUCTOS_FILTRADOS ---------

def obtener_productos_filtrados(correo, categoria):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        u.nombre AS nombre_cliente,
        p.NombreProducto,
        p.PrecioUnidad,
        ip.ruta AS ImagenURL,
        c.NombreCategoria
    FROM Usuario u
    JOIN Cliente cl ON u.ID_Usuario = cl.ID_Usuario
    JOIN Pedido pe ON cl.ID_Cliente = pe.ID_Cliente
    JOIN Detalles_De_Pedido dp ON pe.ID_Pedido = dp.ID_Pedido
    JOIN Producto p ON dp.ID_Producto = p.ID_Producto
    JOIN Categorias c ON p.ID_Categoria = c.ID_Categoria
    LEFT JOIN ImagenProducto ip ON p.ID_Producto = ip.ID_Producto
    WHERE u.correo = %s

    UNION

    SELECT
        '' AS nombre_cliente,
        p2.NombreProducto,
        p2.PrecioUnidad,
        ip2.ruta AS ImagenURL,
        c2.NombreCategoria
    FROM Producto p2
    JOIN Categorias c2 ON p2.ID_Categoria = c2.ID_Categoria
    LEFT JOIN ImagenProducto ip2 ON p2.ID_Producto = ip2.ID_Producto
    WHERE c2.NombreCategoria = %s
    """

    cursor.execute(query, (correo, categoria))
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()

    if not resultados:
        return "", []

    nombre_cliente = ""
    for fila in resultados:
        if fila[0]:
            nombre_cliente = fila[0]
            break

    productos = []
    for row in resultados:
        productos.append({
            'producto': row[1],
            'precio': float(row[2]),
            'imagen': row[3] or '',
            'categoria': row[4]
        })

    return nombre_cliente, productos


# --------- ASIGNAR_EMPLEADO ---------


def asignar_empleado():
    pedido_ids = request.form['pedido_id'].split(",")
    empleado_id = request.form['empleado_id']

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    mensajes = []
    for pid in pedido_ids:

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


def obtener_comentarios_agrupados():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT pedido_id, texto, fecha
        FROM comentarios
        ORDER BY pedido_id, fecha
    """

    cursor.execute(query)
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()

    comentarios_por_pedido = {}

    for comentario in resultados:
        pid = comentario["pedido_id"]
        if pid not in comentarios_por_pedido:
            comentarios_por_pedido[pid] = []
        comentarios_por_pedido[pid].append(comentario)

    return comentarios_por_pedido


# --------- OBTENER_PRODUCTOS ---------

def obtener_productos():
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT
            p.ID_Producto,
            p.NombreProducto,
            p.Stock,
            p.Material,
            p.Color,
            p.PrecioUnidad,
            c.NombreCategoria,
            pr.NombreEmpresa,
            ip.ruta
        FROM Producto p
        LEFT JOIN Categorias c ON p.ID_Categoria = c.ID_Categoria
        LEFT JOIN Proveedor pr ON p.ID_Proveedor = pr.ID_Proveedor
        LEFT JOIN ImagenProducto ip ON p.ID_Producto = ip.ID_Producto
    """
    cursor.execute(query)
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()

    productos = []
    for row in resultados:
        productos.append({
            "id": row[0],
            "nombre": row[1],
            "stock": row[2],
            "material": row[3],
            "color": row[4],
            "precio": float(row[5]),
            "categoria": row[6],
            "proveedor": row[7],
            "imagen": row[8] or ""
        })
    return productos


# --------- ASIGNAR_CALENDARIO ---------
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
            cursor.execute("""SELECT Instalacion FROM Pedido WHERE
                           ID_Pedido = %s""", (pedido_id,))
            instalacion = cursor.fetchone()[0]

            intervalo = timedelta(minutes=60) if instalacion == """
            si""" else timedelta(minutes=30)

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
                    "message": f"""⚠️ El empleado ya tiene una cita el {fecha}
                    a las {start_datetime.strftime('%H:%M')}."""
                })

            # 🟢 Guardamos en la tabla Pedido
            cursor.execute("""
                UPDATE Pedido
                SET ID_Empleado = %s,
                    FechaEntrega = %s,
                    HoraEntrega = %s
                WHERE ID_Pedido = %s
            """, (empleado_id, fecha, start_datetime.strftime("%H:%M:%S"),
                  pedido_id))

            # 🟢 Insertar también en la tabla Calendario
            cursor.execute("""
                INSERT INTO Calendario (Fecha, Hora, Ubicacion, ID_Usuario,
                ID_Pedido, Tipo)
                SELECT %s, %s, u.Direccion, %s, p.ID_Pedido, p.Instalacion
                FROM Pedido p
                JOIN Usuario u ON p.ID_Usuario = u.ID_Usuario
                WHERE p.ID_Pedido = %s
            """, (fecha, start_datetime.strftime("%H:%M:%S"), empleado_id,
                  pedido_id))

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


def buscar_pedidos():
    filtros = []
    fecha = request.form.get("fecha_pedido")
    id_pedido = request.form.get("id_pedido")
    nombre_empleado = request.form.get("nombre_empleado")
    nombre_cliente = request.form.get("nombre_cliente")

    if fecha:
        filtros.append(Pedido.FechaPedido == fecha)

    if id_pedido:
        filtros.append(Pedido.ID_Pedido == id_pedido)

    if nombre_empleado:
        filtros.append(Usuario.Nombre.ilike(f"%{nombre_empleado}%"))

    if nombre_cliente:
        filtros.append(Pedido.Nombre_Cliente.ilike(f"%{nombre_cliente}%"))

    pedidos = (
        Pedido.query
        .join(Usuario, Pedido.ID_Empleado == Usuario.ID_Usuario)
        .filter(and_(*filtros))
        .all()
    )

    resultados = []
    for pedido in pedidos:

        # ➜ Cambiar: devolver lista de productos en lugar de HTML
        productos_lista = []
        detalles = Detalle_Pedido.query.filter_by(
            ID_Pedido=pedido.ID_Pedido).all()

        for detalle in detalles:
            producto = Producto.query.get(detalle.ID_Producto)
            productos_lista.append({
                "producto": producto.NombreProducto,
                "cantidad": detalle.Cantidad
            })

        resultados.append({
            "fecha": str(pedido.FechaEntrega),
            "cliente": f"{pedido.usuario.Nombre} {pedido.usuario.Apellido or ''}",
            "direccion": pedido.Destino,
            "productos": productos_lista,
            "empleado": (
                f"{pedido.empleado.Nombre} {pedido.empleado.Apellido or ''}"
                if pedido.empleado else "Sin asignar"
            ),
            "estado": pedido.Estado
        })

    return resultados


# ----------- ACTUALIZAR PEDIDO -----------
def actualizar_pedido(form_data):
    try:
        pedido_id = int(form_data.get("pedido_id"))
        nuevo_estado = form_data.get("estado")
        texto_comentario = form_data.get("comentario", "").strip()

        pedido = Pedido.query.get(pedido_id)
        if not pedido:
            return {"success": False, "error": "Pedido no encontrado"}

        # Actualiza estado del pedido
        pedido.Estado = nuevo_estado
        db.session.add(pedido)

        # Inserta comentario si no está vacío
        if texto_comentario:
            comentario = Comentarios(
                pedido_id=pedido_id,
                texto=texto_comentario,
                fecha=datetime.utcnow()
            )
            db.session.add(comentario)

        db.session.commit()

        return {"success": True, "message": f"""Pedido {pedido_id}
                actualizado correctamente"""}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}


def registrar_pedido(nombre_comprador, fecha_entrega, hora_entrega, destino,
                     usuario_id, productos):
    try:
        pedido = Pedido(
            NombreComprador=nombre_comprador,
            Estado="pendiente",
            FechaPedido=datetime.now(),
            FechaEntrega=fecha_entrega,
            HoraEntrega=hora_entrega,
            Destino=destino,
            ID_Usuario=usuario_id
        )
        db.session.add(pedido)
        db.session.flush()  # obtiene ID_Pedido

        for prod in productos:
            detalle = Detalle_Pedido(
                ID_Pedido=pedido.ID_Pedido,
                ID_Producto=prod["id_producto"],
                Cantidad=prod["cantidad"],
                PrecioUnidad=prod["precio"]
            )
            db.session.add(detalle)

        db.session.commit()
        return {"success": True, "pedido_id": pedido.ID_Pedido}

    except Exception as e:
        db.session.rollback()
        return {"success": False, "message": str(e)}


def registrar_firma(pedido_id, nombre_cliente, ruta_firma):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO firmas (pedido_id, nombre_cliente, firma)
        VALUES (%s, %s, %s)
    """, (pedido_id, nombre_cliente, ruta_firma))
    conn.commit()
    cursor.close()
    conn.close()


def guardar_producto(data, files):
    conn = get_connection()
    cursor = conn.cursor()

    # Insertar producto
    cursor.execute("""
        INSERT INTO producto (NombreProducto, Stock, Material, Color,
        PrecioUnidad, ID_Categoria, ID_Proveedor)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (data['NombreProducto'], data['Stock'], data['Material'],
          data['Color'], data['PrecioUnidad'], data['ID_Categoria'],
          data['ID_Proveedor']))
    conn.commit()
    producto_id = cursor.lastrowid

    # Guardar imágenes
    for file in files:
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'],
                                    filename)
            file.save(filepath)

            image_url = f"/static/img/{filename}"

            cursor.execute("""
                INSERT INTO imagenproducto (ID_Producto, ruta)
                VALUES (%s, %s)
            """, (producto_id, image_url))
        conn.commit()
    return producto_id


def guardar_producto_route():
    try:
        # ✅ Guardar datos del producto primero
        cursor = get_connection.cursor()
        cursor.execute("""
            INSERT INTO producto (NombreProducto, Stock, StockMinimo, Material, Color,
                                PrecioUnidad, ID_Categoria, ID_Proveedor)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            request.form['NombreProducto'],
            int(request.form['Stock']),
            int(request.form.get('StockMinimo', 0)),  # <- asegura un valor por defecto
            request.form['Material'],
            request.form['Color'],
            float(request.form['PrecioUnidad']),
            int(request.form['ID_Categoria']),
            int(request.form['ID_Proveedor'])
        ))

        producto_id = cursor.lastrowid

        # ✅ Guardar imágenes
        if 'imagenes' in request.files:
            files = request.files.getlist('imagenes')
            for file in files:
                if file and file.filename != '':
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(
                        current_app.config['UPLOAD_FOLDER'], filename)

                    # Guardar físicamente en static/img
                    file.save(filepath)

                    image_url = f"static/img/{filename}"

                    cursor.execute("""
                        INSERT INTO imagenproducto (ID_Producto, Imagen)
                        VALUES (%s, %s)
                    """, (producto_id, image_url))

        db.connection.commit()
        return jsonify({"success": True,
                        "message": "Producto guardado con éxito"})

    except Exception as e:
        db.connection.rollback()
        return jsonify({"success": False, "message": str(e)})


def get_productos():
    conn = get_connection()
    query = """
        SELECT 
            p.ID_Producto,
            p.NombreProducto,
            p.Stock,
            p.StockMinimo,
            p.Material,
            p.PrecioUnidad,
            p.Color,
            (SELECT i.ruta
             FROM imagenproducto i
             WHERE i.ID_Producto = p.ID_Producto
             LIMIT 1) AS Imagen
        FROM producto p;
    """

    cursor = conn.cursor(dictionary=True)
    cursor.execute(query)
    productos = cursor.fetchall()
    cursor.close()
    conn.close()
    return productos


def get_producto_by_id(id_producto):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT p.ID_Producto, p.Stock, p.NombreProducto, p.Material,
               p.PrecioUnidad, p.Color, p.Garantia,
               c.NombreCategoria, pr.NombreEmpresa,
               i.ruta AS Imagen
        FROM producto p
        LEFT JOIN categorias c ON p.ID_Categoria = c.ID_Categoria
        LEFT JOIN proveedor pr ON p.ID_Proveedor = pr.ID_Proveedor
        LEFT JOIN imagenproducto i ON i.ID_Producto = p.ID_Producto
        WHERE p.ID_Producto = %s
    """
    cursor.execute(query, (id_producto,))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    if not rows:
        return None

    # Tomar datos del producto de la primera fila
    producto = {
        "ID_Producto": rows[0]["ID_Producto"],
        "Stock": rows[0]["Stock"],
        "NombreProducto": rows[0]["NombreProducto"],
        "Material": rows[0]["Material"],
        "PrecioUnidad": rows[0]["PrecioUnidad"],
        "Color": rows[0]["Color"],
        "Garantia": rows[0]["Garantia"],  # <-- agregada la garantía
        "NombreCategoria": rows[0]["NombreCategoria"],
        "NombreEmpresa": rows[0]["NombreEmpresa"],
        # Limpiar rutas para que sean relativas a /static/
        "Imagenes": [
            row["Imagen"].replace("static/", "") for row in rows if row["Imagen"]
        ]
    }

    return producto


def obtener_pedidos_por_cliente(id_usuario):
    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    # 1️⃣ Obtener todos los pedidos del usuario
    cursor.execute("""
        SELECT *
        FROM pedido
        WHERE ID_Usuario = %s
        ORDER BY FechaPedido DESC
    """, (id_usuario,))
    pedidos = cursor.fetchall()

    # 2️⃣ Agregar detalles a cada pedido
    for pedido in pedidos:
        cursor.execute("""
            SELECT
                dp.id_producto,
                dp.cantidad,
                p.NombreProducto,
                p.PrecioUnidad,
                COALESCE(ip.ruta, '') AS Imagen
            FROM detalle_pedido dp
            JOIN producto p ON dp.id_producto = p.id_producto
            LEFT JOIN imagenproducto ip ON p.id_producto = ip.id_producto
            WHERE dp.ID_Pedido = %s
            GROUP BY dp.id_producto
        """, (pedido['ID_Pedido'],))

        detalles = cursor.fetchall()

        # 3️⃣ Limpiar rutas de imágenes
        for item in detalles:
            if item['Imagen']:
                item['Imagen'] = item['Imagen'].replace("static/", "")

        # 4️⃣ Calcular total del pedido
        total = sum(item['cantidad'] * float(item[
            'PrecioUnidad']) for item in detalles)

        pedido['detalles'] = detalles
        pedido['total'] = round(total, 2)

    conexion.close()
    return pedidos


def crear_pedido_y_pago(id_usuario, carrito, metodo_pago, monto_total, destino):
    db = get_connection()
    cursor = db.cursor()

    try:
        # 1️⃣ Insertar el pedido principal
        cursor.execute("""
            INSERT INTO pedido (Estado, FechaPedido, Destino, ID_Usuario)
            VALUES (%s, NOW(), %s, %s);
        """, ('pendiente', destino, id_usuario))

        # Obtener el ID del pedido recién insertado
        pedido_id = cursor.lastrowid

        # 2️⃣ Insertar los productos en detalle_pedido
        for item in carrito:
            cursor.execute("""
                INSERT INTO detalle_pedido (ID_Pedido, ID_Producto, Cantidad, PrecioUnidad)
                VALUES (%s, %s, %s, %s);
            """, (
                pedido_id,
                item.get("id"),          # Asegúrate de que el producto tenga "id" en el JSON
                item.get("quantity", 1),
                item.get("price", 0)
            ))

        # 3️⃣ Insertar registro de pago
        cursor.execute("""
            INSERT INTO pagos (MetodoPago, FechaPago, Monto, ID_Pedido)
            VALUES (%s, NOW(), %s, %s);
        """, (metodo_pago, monto_total, pedido_id))

        db.commit()
        print("✅ Pedido y pago registrados correctamente.")
        return pedido_id

    except Exception as e:
        db.rollback()
        print("💥 Error al crear pedido y pago:", e)
        raise e

    finally:
        cursor.close()
        db.close()


def obtener_eventos():
    """Devuelve todos los eventos registrados en la base de datos."""
    return [evento.to_dict() for evento in Calendario.query.all()]


def obtener_evento_por_id(id_calendario):
    """Obtiene un evento específico por su ID."""
    return Calendario.query.get(id_calendario)


def crear_evento(data):
    """Crea un nuevo registro en el calendario."""
    try:
        nuevo = Calendario(
            Fecha=datetime.strptime(data['Fecha'], '%Y-%m-%d').date(),
            Hora=datetime.strptime(data['Hora'], '%H:%M').time(),
            Ubicacion=data.get('Ubicacion', ''),
            Tipo=data.get('Tipo', 'Instalación'),
            ID_Usuario=data.get('ID_Usuario'),
            ID_Pedido=data.get('ID_Pedido')
        )
        db.session.add(nuevo)
        db.session.commit()
        return {"mensaje": "Evento agregado correctamente",
                "id": nuevo.ID_Calendario}
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Error al crear el evento: {e}")


def editar_evento(id_calendario, data):
    """Actualiza un evento existente."""
    evento = Calendario.query.get(id_calendario)
    if not evento:
        raise Exception("Evento no encontrado")

    try:
        evento.Fecha = datetime.strptime(data['Fecha'], '%Y-%m-%d').date()
        evento.Hora = datetime.strptime(data['Hora'], '%H:%M').time()
        evento.Ubicacion = data.get('Ubicacion', evento.Ubicacion)
        evento.Tipo = data.get('Tipo', evento.Tipo)
        db.session.commit()
        return {"mensaje": "Evento actualizado correctamente"}
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Error al actualizar el evento: {e}")


def eliminar_evento(id_calendario):
    """Elimina un evento del calendario."""
    evento = Calendario.query.get(id_calendario)
    if not evento:
        raise Exception("Evento no encontrado")

    try:
        db.session.delete(evento)
        db.session.commit()
        return {"mensaje": "Evento eliminado correctamente"}
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Error al eliminar el evento: {e}")


def recivo(pedido_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            pg.ID_Pagos, pg.MetodoPago, pg.FechaPago, pg.Monto, 
            dp.cantidad, dp.PrecioUnidad, pr.NombreProducto
        FROM pagos pg
        INNER JOIN pedido p ON pg.ID_Pedido = p.ID_Pedido
        INNER JOIN detalle_pedido dp ON dp.ID_Pedido = p.ID_Pedido
        INNER JOIN producto pr ON pr.ID_Producto = dp.ID_Producto
        WHERE p.ID_Pedido = %s
    """, (pedido_id,))
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados


def generar_estadisticas_reseñas():

    data = {}

    # -----------------------------------------------------------
    # 1️⃣ Promedio general y total de reseñas
    # -----------------------------------------------------------
    promedio = db.session.query(func.avg(Reseñas.Estrellas)).scalar()
    total = db.session.query(func.count(Reseñas.ID_Reseña)).scalar()

    data["promedio_general"] = round(promedio or 0, 2)
    data["total"] = total or 0

    # -----------------------------------------------------------
    # 2️⃣ Distribución por estrellas
    # -----------------------------------------------------------
    estrellas = db.session.query(
        Reseñas.Estrellas,
        func.count(Reseñas.ID_Reseña)
    ).group_by(Reseñas.Estrellas).all()

    # Inicia en 0 para que siempre existan 5 valores
    arr = [0, 0, 0, 0, 0]

    for estrella, cantidad in estrellas:
        if 1 <= estrella <= 5:
            arr[estrella - 1] = cantidad

    data["por_estrellas"] = arr

    # -----------------------------------------------------------
    # 3️⃣ Promedios por mes (últimos 12 meses)
    # -----------------------------------------------------------
    por_mes = db.session.query(
        func.date_format(Reseñas.Fecha, "%Y-%m").label("mes"),
        func.avg(Reseñas.Estrellas)
    ).group_by("mes").order_by("mes").all()

    meses_legibles = []
    meses_nombres = {
        "01": "Enero", "02": "Febrero", "03": "Marzo",
        "04": "Abril", "05": "Mayo", "06": "Junio",
        "07": "Julio", "08": "Agosto", "09": "Septiembre",
        "10": "Octubre", "11": "Noviembre", "12": "Diciembre"
    }

    for mes, promedio in por_mes:
        y, m = mes.split("-")
        meses_legibles.append({
            "mes": f"{meses_nombres[m]} {y}",
            "promedio": round(promedio, 2)
        })

    data["por_mes"] = meses_legibles

    # -----------------------------------------------------------
    # 4️⃣ Comparativa por tipo
    # -----------------------------------------------------------
    tipo_counts = db.session.query(
        Reseñas.tipo,
        func.count(Reseñas.ID_Reseña)
    ).group_by(Reseñas.tipo).all()

    por_tipo = {"producto": 0, "pedido": 0}

    for tipo, cant in tipo_counts:
        if tipo == "producto":
            por_tipo["producto"] = cant
        elif tipo == "pedido":
            por_tipo["pedido"] = cant

    data["por_tipo"] = por_tipo

    # -----------------------------------------------------------
    # 5️⃣ Comentarios negativos (estrellas <= 2)
    # -----------------------------------------------------------
    negativos = db.session.query(
        Reseñas.ID_Referencia,
        Reseñas.Comentario
    ).filter(Reseñas.Estrellas <= 2).all()

    lista_neg = [
        {"pedido": ped, "comentario": com}
        for ped, com in negativos
    ]

    data["negativos"] = lista_neg

    return data


def obtener_estadisticas_pedidos_por_mes():
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            pe.FechaPedido,
            SUM(dp.Cantidad * p.PrecioUnidad) AS total_ventas,
            SUM(dp.Cantidad) AS total_productos
        FROM Pedido pe
        JOIN Detalle_Pedido dp ON pe.ID_Pedido = dp.ID_Pedido
        JOIN Producto p ON dp.ID_Producto = p.ID_Producto
        WHERE pe.Estado IN ('completado', 'en proceso')
        GROUP BY pe.ID_Pedido, pe.FechaPedido
        ORDER BY pe.FechaPedido;
    """

    cursor.execute(query)
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()

    estadisticas = defaultdict(lambda: {
        "total_ventas": 0,
        "total_productos": 0,
        "cantidad_pedidos": 0,
        "promedio": 0
    })

    for fecha, total_ventas, total_productos in resultados:
        clave_mes = fecha.strftime("%Y-%m")

        estadisticas[clave_mes]["total_ventas"] += float(total_ventas)
        estadisticas[clave_mes]["total_productos"] += int(total_productos)
        estadisticas[clave_mes]["cantidad_pedidos"] += 1

    # Calcular promedios
    for mes in estadisticas:
        pedidos = estadisticas[mes]["cantidad_pedidos"]
        estadisticas[mes]["promedio"] = round(
            estadisticas[mes]["total_ventas"] / pedidos, 2
        )

        estadisticas[mes]["total_ventas"] = round(
            estadisticas[mes]["total_ventas"], 2
        )

    return dict(estadisticas)


def obtener_dispositivo():
    ua = request.headers.get("User-Agent", "").lower()

    if "mobile" in ua:
        return "📱 Teléfono móvil"
    elif "windows" in ua:
        return "💻 Windows"
    elif "mac" in ua:
        return "💻 Mac"
    elif "linux" in ua:
        return "💻 Linux"
    else:
        return "Dispositivo desconocido"


def enviar_correo_seguridad(correo, intento):
    dispositivo = obtener_dispositivo()

    link_si = url_for(
        'auth.confirmar_dispositivo',
        intento_id=intento.id,
        accion='si',
        _external=True
    )

    link_no = url_for(
        'auth.confirmar_dispositivo',
        intento_id=intento.id,
        accion='no',
        _external=True
    )

    msg = Message(
        subject="⚠️ Alerta de seguridad - Intentos de acceso",
        recipients=[correo]
    )

    msg.html = f"""
    <h3>⚠️ Intento de acceso detectado</h3>
    <p>Están intentando acceder a tu cuenta desde:</p>
    <ul>
        <li><b>Dispositivo:</b> {dispositivo}</li>
        <li><b>IP:</b> {intento.ip}</li>
        <li><b>Fecha:</b> {datetime.now()}</li>
    </ul>

    <p><b>¿Eres tú?</b></p>

    <a href="{link_si}"
       style="padding:10px;background:green;color:white;text-decoration:none;">
       ✔ Sí
    </a>

    <a href="{link_no}"
       style="padding:10px;background:red;color:white;text-decoration:none;">
       ❌ No
    </a>
    """

    mail.send(msg)

