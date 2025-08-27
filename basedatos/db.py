from flask import Flask, request, jsonify, session
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = 'mi_clave_secreta'

# 🔧 Configuración de conexión MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'       # tu usuario
app.config['MYSQL_PASSWORD'] = ''       # tu contraseña de MySQL
app.config['MYSQL_DB'] = 'Tienda_Casa_en_el_arbol'

mysql = MySQL(app)

# ==============================
# REGISTRO DE USUARIO
# ==============================
@app.route('/registro', methods=['POST'])
def registro():
    data = request.json
    nombre = data.get('Nombre')
    telefono = data.get('Telefono')
    correo = data.get('Correo')
    direccion = data.get('Direccion')
    contrasena = data.get('Contraseña')
    rol = data.get('Rol')

    if not nombre or not correo or not contrasena:
        return jsonify({'mensaje': 'Faltan datos'}), 400

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO Usuario (ID_Usuario, Nombre, Telefono, Correo, Direccion, Contraseña, Rol, Activo)
        VALUES (NULL, %s, %s, %s, %s, %s, %s, TRUE)
    """, (nombre, telefono, correo, direccion, contrasena, rol))
    mysql.connection.commit()
    cur.close()

    return jsonify({'mensaje': 'Usuario registrado con éxito'}), 201


# ==============================
# LOGIN DE USUARIO
# ==============================
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    correo = data.get('Correo')
    contrasena = data.get('Contraseña')

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM Usuario WHERE Correo=%s AND Contraseña=%s", (correo, contrasena))
    user = cur.fetchone()
    cur.close()

    if user:
        session['usuario'] = user['Correo']
        return jsonify({'mensaje': f"Bienvenido {user['Nombre']}!"})
    else:
        return jsonify({'mensaje': 'Usuario o contraseña incorrectos'}), 401


# ==============================
# PERFIL (requiere login)
# ==============================
@app.route('/perfil')
def perfil():
    if 'usuario' in session:
        return jsonify({'mensaje': f"Estás logueado como {session['usuario']}"})
    return jsonify({'mensaje': 'Debes iniciar sesión'}), 401


if __name__ == '__main__':
    app.run(port=3000, debug=True)
