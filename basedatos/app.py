from flask import Flask , Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL


app = Flask(__name__)
app.secret_key = "clave_secreta"  


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'Tienda_Casa_en_el_arbol'


mysql = MySQL(app)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        contrasena = request.form['contrasena']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM Usuario WHERE Correo = %s', (correo,))
        user = cursor.fetchone()

        if user:
            flash("⚠️ El correo ya está registrado", "danger")
        else:
            cursor.execute(
                "INSERT INTO Usuario (Nombre, Telefono, Correo, Direccion, Contraseña, Rol, Activo) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (nombre, telefono, correo, direccion, contrasena, "cliente", True)
            )
            mysql.connection.commit()
            flash("✅ Registro exitoso, ya puedes iniciar sesión", "success")
            return redirect(url_for('login'))

    return render_template("registro.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contrasena = request.form['contrasena']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM Usuario WHERE Correo = %s AND Contraseña = %s', (correo, contrasena))
        user = cursor.fetchone()

        if user:
            session['loggedin'] = True
            session['id_usuario'] = user['ID_Usuario']
            session['nombre'] = user['Nombre']
            flash("✅ Bienvenido " + user['Nombre'], "success")
            return redirect(url_for('dashboard'))
        else:
            flash("❌ Correo o contraseña incorrectos", "danger")

    return render_template("login.html")

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        correo = request.form['correo']
        nueva_contrasena = request.form['nueva_contrasena']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM Usuario WHERE Correo = %s", (correo,))
        user = cursor.fetchone()

        if user:
            cursor.execute("UPDATE Usuario SET Contraseña = %s WHERE Correo = %s", (nueva_contrasena, correo))
            mysql.connection.commit()
            flash("✅ Contraseña actualizada, ahora inicia sesión", "success")
            return redirect(url_for('login'))
        else:
            flash("⚠️ El correo no está registrado", "danger")

    return render_template("olvidaste_contraseña.html")

