from flask import Flask , request, render_template, redirect, url_for, flash
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

    return render_template("register.html")

