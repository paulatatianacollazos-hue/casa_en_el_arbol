import os
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from datetime import datetime
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import re



from flask_login import (
    LoginManager, login_required, current_user,
    login_user, logout_user
)


from functools import wraps

from basedatos.models import db, Usuario, Direccion, Notificaciones, Calendario,Producto,Pedido, Detalle_Pedido
# ------------------ CONFIG ------------------ #
app = Flask(__name__)
instalaciones = []
reviews=[]

app.config['SECRET_KEY'] = "mi_clave_super_secreta_y_unica"

DB_URL = 'mysql+pymysql://root:2426@127.0.0.1:3306/Tienda_db'
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'casaenelarbol236@gmail.com'
app.config['MAIL_PASSWORD'] = 'usygdligtlewedju'
app.config['MAIL_DEFAULT_SENDER'] = ('Casa en arbol', app.config['MAIL_USERNAME'])

mail = Mail(app)
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
db.init_app(app)

# ------------------ FLASK-LOGIN ------------------ #
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# ------------------ DECORADOR DE ROLES ------------------ #
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("⚠️ Debes iniciar sesión para acceder.", "warning")
                return redirect(url_for("login"))
            if current_user.Rol.lower() not in [r.lower() for r in roles]:
                flash("❌ No tienes permisos para acceder a esta página.", "danger")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return wrapped
    return decorator





# ------------------ FUNCIONES ------------------ #
def crear_notificacion(user_id, titulo, mensaje):
    noti = Notificaciones(
        ID_Usuario=user_id,
        Titulo=titulo,
        Mensaje=mensaje
    )
    db.session.add(noti)
    db.session.commit()

def send_reset_email(user_email, user_name, token):
    reset_url = url_for('reset_password', token=token, _external=True)
    msg = Message(
        subject="Restablece tu contraseña - Casa en Arbol",
        recipients=[user_email],
        html=render_template('email_reset.html', user_name=user_name, reset_url=reset_url)
    )
    mail.send(msg)

def get_connection():
    return mysql.connector.connect(
        user='root',
        password='2426',
        host='localhost',
        database='tienda_db',
       
    )


def obtener_todos_los_pedidos():
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            pe.ID_Pedido,
            u.Nombre AS nombre_usuario,
            u.Telefono,
            u.Direccion,
            p.ID_Producto,
            p.NombreProducto,
            dp.Cantidad,
            pe.FechaPedido,
            ip.ruta AS ImagenURL,
            p.PrecioUnidad,
            pe.ID_Empleado
        FROM Pedido pe
        JOIN Usuario u ON pe.ID_Usuario = u.ID_Usuario
        JOIN Detalle_Pedido dp ON pe.ID_Pedido = dp.ID_Pedido
        JOIN Producto p ON dp.ID_Producto = p.ID_Producto
        LEFT JOIN ImagenProducto ip ON p.ID_Producto = ip.ID_Producto
        ORDER BY pe.FechaPedido DESC
    """

    cursor.execute(query)
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()

    pedidos_dict = {}

    for row in resultados:
        id_pedido = row[0]
        id_producto = row[4]

        producto = {
            'id': id_producto,
            'nombre': row[5],
            'cantidad': row[6],
            'imagen': row[8] or '',
            'precio': float(row[9])  # Asegura que el precio esté como número
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
                'id_empleado': row[10]   # 👈 nuevo campo
            }

        productos = pedidos_dict[id_pedido]['productos']

        if id_producto in productos:
            productos[id_producto]['cantidad'] += producto['cantidad']
        else:
            productos[id_producto] = producto

    for pedido in pedidos_dict.values():
        pedido['productos'] = list(pedido['productos'].values())
        total = sum(prod['cantidad'] * prod['precio']
                    for prod in pedido['productos'])
        pedido['total'] = round(total, 2)  # Puedes redondear a 2 decimales
    return list(pedidos_dict.values())


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
            dp.Cantidad
        FROM Pedido p
        JOIN Usuario u ON p.ID_Usuario = u.ID_Usuario
        JOIN Detalle_Pedido dp ON p.ID_Pedido = dp.ID_Pedido
        JOIN Producto pr ON dp.ID_Producto = pr.ID_Producto
    """)
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()

    agrupado = {}
    for row in resultados:
        pid = row['ID_Pedido']
        if pid not in agrupado:
            agrupado[pid] = {
                'Nombre_Cliente': row['Nombre_Cliente'],
                'Telefono': row['Telefono'],
                'Direccion': row['Direccion'],
                'Productos': []
            }
        agrupado[pid]['Productos'].append({
            'Producto': row['Producto'],
            'Cantidad': row['Cantidad']
        })

    return agrupado  # Retorna un dict con ID_Pedido como clave


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


@app.route('/envios')
@login_required
@role_required('admin')
def envios():
    pedidos = obtener_todos_los_pedidos()
    detalles = detalle()
    empleados = obtener_empleados()
    return render_template('administrador/envios.html', pedidos=pedidos, detalles=detalles,
                           empleados=empleados)


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


@app.route("/control_pedidos")
@login_required
@role_required('admin')
def control_pedidos():
    pedidos = todos_los_pedidos()
    return render_template('administrador/control_pedidos.html', pedidos=pedidos)


@app.route('/asignar_empleado', methods=['POST'])
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

# 2️⃣ verificar si el empleado ya tiene un pedido en el mismo rango de 30 min
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


@app.route('/actualizar_pedido', methods=['POST'])
def actualizar_pedido():
    pedido_id = request.form['pedido_id']
    nuevo_estado = request.form['estado']
    comentario = request.form['comentario']

    conn = get_connection()  # ← esta es la forma correcta
    cursor = conn.cursor()

    try:
        # Actualizar estado del pedido
        cursor.execute("""
            UPDATE Pedido
            SET Estado = %s
            WHERE ID_Pedido = %s
        """, (nuevo_estado, pedido_id))

        # Insertar comentario (si se escribió algo)
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

    return redirect(url_for('control_pedidos'))  # O la vista que desees


@app.route('/estado', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def buscar_pedido():
    if request.method == 'POST':
        pedido_id = request.form['pedido_id']
        return redirect(url_for('administrador/control_pedidos.html', pedido_id=pedido_id))
    return render_template('administrador/estado.html')


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


@app.route('/comentarios')
@login_required
@role_required('admin')
def mostrar_comentarios():
    comentarios = obtener_comentarios_agrupados()
    return render_template('administrador/comentarios.html', comentarios=comentarios)


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


def obtener_producto_por_id(producto_id):
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
        WHERE p.ID_Producto = %s
    """
    cursor.execute(query, (producto_id,))
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()

    if not resultados:
        return None

    producto = {
        "id": resultados[0][0],
        "nombre": resultados[0][1],
        "stock": resultados[0][2],
        "material": resultados[0][3],
        "color": resultados[0][4],
        "precio": float(resultados[0][5]),
        "categoria": resultados[0][6],
        "proveedor": resultados[0][7],
        "imagenes": [row[8] for row in resultados if row[8]]
    }
    return producto


@app.route('/productos')
def listar_productos():
    productos = obtener_productos()
    return render_template('productos.html', productos=productos)


@app.route('/producto/<int:producto_id>')
def ver_producto(producto_id):
    producto = obtener_producto_por_id(producto_id)
    if not producto:
        return "Producto no encontrado", 404
    return render_template('detalles.html', producto=producto)


@app.route('/firmar', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def firmar_pedido():
    mensaje = None

    if request.method == 'POST':
        pedido_id = request.form['pedido_id']
        nombre = request.form['nombre_cliente']
        archivo = request.files.get('firma')  # 👈 cambio importante

        if archivo and archivo.filename != "":
            filename = secure_filename(archivo.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            archivo.save(filepath)

            ruta_db = f"firmas/{filename}"

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO firmas (pedido_id, nombre_cliente, firma)
                VALUES (%s, %s, %s)
            """, (pedido_id, nombre, ruta_db))
            conn.commit()
            cursor.close()
            conn.close()

            mensaje = "Firma registrada correctamente "
        else:
            mensaje = "No se subió ningún archivo "

    return render_template('administrador/confirmacion_firma.html', mensaje=mensaje)


@app.route('/reporte', methods=['GET', 'POST'])
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


@app.route("/asignar_calendario", methods=["POST"])
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


# ------------------ RUTAS ------------------ #
@app.route('/')
def index():
    return render_template('index.html')

# ------------------Catalogo ------------------ #

@app.route('/catalogo')
@login_required
def catalogo():
    productos = Producto.query.all() 
    return render_template("catalogo.html", productos=productos)


@app.route("/pagos")
def pagos():
    return render_template("pagos.html")

@app.route("/estadisticas")
def estadisticas():
    return render_template("administrador/estadisticas.html")

# ------------------ MAIN ------------------ #
if __name__ == '__main__':
    app.run(debug=True)