from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Usuario
from datetime import datetime

app = Flask(__name__)
app.secret_key = "clave_secreta"

# Configuración de la base de datos MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1:3306/Tienda_casa_en_el_arbol'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Crear tablas
with app.app_context():
    db.create_all()


# Rutas
@app.route('/')
def index():
    return render_template("index.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        correo = request.form["correo"]
        password = request.form["password"]

        usuario = Usuario.query.filter_by(Correo=correo).first()

        if usuario and check_password_hash(usuario.Contrasena, password):
            session["usuario"] = usuario.Nombre
            flash(f"Bienvenido {usuario.Nombre}", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Correo o contraseña incorrectos", "danger")

    return render_template("login.html")


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == "POST":
        Nombre = request.form["nombre"]
        Correo = request.form["correo"]
        Telefono = request.form["telefono"]
        Contrasena  = generate_password_hash(request.form["password"])

        nuevo_usuario = Usuario(
            Nombre=Nombre,
            Correo= Correo,
            Telefono= Telefono,
            Contrasena= Contrasena,
            Activo=True,
            Rol="cliente"
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        flash("Usuario registrado con éxito", "success")
        return redirect(url_for("login"))

    return render_template("registro.html")


@app.route('/dashboard')
def dashboard():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", usuario=session["usuario"])


@app.route('/logout')
def logout():
    session.pop("usuario", None)
    flash("Has cerrado sesión", "info")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
