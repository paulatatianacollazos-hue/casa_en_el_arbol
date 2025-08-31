from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, Usuario  # importa db y los modelos
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "clave_secreta"

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///basedatos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Crear las tablas
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

        if usuario and check_password_hash(usuario.Contraseña, password):
            session["usuario"] = usuario.Nombre
            flash("Bienvenido " + usuario.Nombre, "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Correo o contraseña incorrectos", "danger")

    return render_template("login.html")

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == "POST":
        nombre = request.form["nombre"]
        correo = request.form["correo"]
        telefono = request.form["telefono"]
        password = generate_password_hash(request.form["password"])

        nuevo_usuario = Usuario(Nombre=nombre, Correo=correo, Telefono=telefono, Contraseña=password, Activo=True, Rol="cliente")
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


if __name__ == "__main__":
    app.run(debug=True)
