import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import request, render_template, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from flask import jsonify

from basedatos.models import db, Usuario , Direccion ,Notificaciones

app = Flask(__name__)
app.config['SECRET_KEY'] = "mi_clave_super_secreta_y_unica"


DB_URL = 'mysql+pymysql://root:@127.0.0.1:3306/Tienda_db'
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

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre_completo = request.form.get('name', '').strip()
        correo = request.form.get('email', '').strip()
        telefono = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()

        if not nombre_completo or not correo or not password:
            flash('Nombre, correo y contraseña son obligatorios.', 'warning')
            return render_template('register.html')

        # Divide nombre en nombre/apellido si quieres guardar algo por defecto
        partes = nombre_completo.split(" ", 1)
        nombre = partes[0]
        apellido = partes[1] if len(partes) > 1 else ""  # vacío si no puso segundo nombre

        usuario_existente = Usuario.query.filter_by(Correo=correo).first()
        if usuario_existente:
            flash('Ya existe una cuenta con ese correo.', 'danger')
            return render_template('register.html')

        nuevo_usuario = Usuario(
        Nombre=nombre,
        Apellido=apellido,
        Telefono=telefono,
        Correo=correo,
        Contraseña=generate_password_hash(password)
    )
        



        db.session.add(nuevo_usuario)
        db.session.commit()

        crear_notificacion(
                user_id=nuevo_usuario.ID_Usuario,
                titulo="¡Bienvenido a Casa en el Árbol!",
                mensaje="Tu cuenta se ha creado correctamente. Explora nuestros productos y promociones."
            )

        flash('Cuenta creada correctamente, ahora puedes completar tu información en el perfil.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Ingresa correo y contraseña')
            return render_template('login.html')

        user = Usuario.query.filter_by(Correo=email).first()
        if user and check_password_hash(user.Contraseña, password):
            nombre = user.Nombre.strip()
            iniciales = ''.join([parte[0] for parte in nombre.split()][:2]).upper()

            session['user_id'] = user.ID_Usuario
            session['username'] = nombre
            session['iniciales'] = iniciales

            session['show_welcome_modal'] = True

            flash('Inicio de sesión exitoso')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales inválidas')
            return render_template('login.html')

    return render_template('login.html')



@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Sesión cerrada correctamente", "info")
    return redirect(url_for('index'))




@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = Usuario.query.filter_by(Correo=email).first()
        if user:
            try:
                token = s.dumps(email, salt='password-recovery')
                send_reset_email(user_email=email, user_name=user.Nombre, token=token)
                flash('📩 Se envió el enlace a tu correo', 'success')
            except Exception as e:
                print(f"Error al enviar correo: {e}")
                flash('❌ No se pudo enviar el correo', 'error')
        else:
            flash('⚠️ Correo no registrado', 'warning')
    return render_template('forgot_password.html')


def send_reset_email(user_email, user_name, token):
    reset_url = url_for('reset_password', token=token, _external=True)
    msg = Message(
        subject="Restablece tu contraseña - Casa en Arbol",
        recipients=[user_email],
        html=render_template('email_reset.html', user_name=user_name, reset_url=reset_url)
    )
    mail.send(msg)






@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        
        email = s.loads(token, salt='password-recovery', max_age=3600).strip().lower()
    except (SignatureExpired, BadSignature):
        flash('❌ Enlace expirado o inválido', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # Validaciones
        if not new_password or not confirm_password:
            flash('⚠️ Completa ambos campos', 'warning')
            return render_template('reset_password.html', token=token)
        if new_password != confirm_password:
            flash('⚠️ Las contraseñas no coinciden', 'warning')
            return render_template('reset_password.html', token=token)

       
        user = Usuario.query.filter_by(Correo=email).first()
        if not user:
            flash('❌ Usuario no encontrado', 'error')
            return redirect(url_for('forgot_password'))


        hashed_password = generate_password_hash(new_password)
        user.Contraseña = hashed_password  

        try:
            db.session.commit()
            flash('✅ Contraseña restablecida. Ahora puedes iniciar sesión con tu nueva contraseña.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            print(f"Error al actualizar contraseña: {e}")
            flash('❌ Hubo un error al actualizar tu contraseña. Inténtalo de nuevo.', 'error')
            return render_template('reset_password.html', token=token)

    return render_template('reset_password.html', token=token)




@app.route('/test_mail')
def test_mail():
    try:
        msg = Message("Prueba", recipients=[app.config['MAIL_USERNAME']])
        msg.body = "✅ Configuración de correo funciona"
        mail.send(msg)
        return "Correo enviado correctamente"
    except Exception as e:
        return f"Error: {e}"
    


@app.route('/actualizacion_datos', methods=['GET', 'POST'])
def actualizacion_datos():
    user_id = session.get('user_id')
    if not user_id:
        flash('Debes iniciar sesión para acceder a esta página.', 'warning')
        return redirect(url_for('login'))

    usuario = Usuario.query.get(user_id)
    if not usuario:
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('login'))

    direcciones = Direccion.query.filter_by(ID_Usuario=user_id).all()

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        genero = request.form.get('genero', '').strip()
        correo = request.form.get('correo', '').strip()
        telefono = request.form.get('telefono', '').strip()
        password = request.form.get('password', '').strip()

        if not nombre or not apellido or not correo:
            flash('Los campos Nombre, Apellido y Correo son obligatorios.', 'warning')
            return render_template('Actualizacion_datos.html', usuario=usuario, direcciones=direcciones)

        usuario_existente = Usuario.query.filter(
            Usuario.Correo == correo,
            Usuario.ID_Usuario != user_id
        ).first()
        if usuario_existente:
            flash('El correo ya está registrado por otro usuario.', 'danger')
            return render_template('Actualizacion_datos.html', usuario=usuario, direcciones=direcciones)

        # Actualiza datos
        usuario.Nombre = nombre
        usuario.Apellido = apellido
        usuario.Genero = genero
        usuario.Correo = correo
        usuario.Telefono = telefono

        if password:
            usuario.Contraseña = generate_password_hash(password)

        try:
            db.session.commit()
            # ✅ Redirige con parámetro para mostrar modal de confirmación
            return redirect(url_for('actualizacion_datos', perfil_guardado=1))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')

  
    perfil_guardado = request.args.get('perfil_guardado', 0, type=int)

    return render_template(
        'Actualizacion_datos.html',
        usuario=usuario,
        direcciones=direcciones,
        perfil_guardado=perfil_guardado
    )



@app.route('/agregar_direccion', methods=['POST'])
def agregar_direccion():
    user_id = session.get('user_id')
    if not user_id:
        flash("Debes iniciar sesión para agregar direcciones.", "warning")
        return redirect(url_for('login'))

    nueva_direccion = Direccion(
        ID_Usuario=user_id,
        Pais="Colombia",
        Departamento="Bogotá, D.C.",
        Ciudad="Bogotá",
        Direccion=request.form.get('direccion'),
        InfoAdicional=request.form.get('infoAdicional'),
        Barrio=request.form.get('barrio'),
        Destinatario=request.form.get('destinatario')
    )
    db.session.add(nueva_direccion)
    db.session.commit()

    # ✅ Redirige con query param para mostrar modal
    return redirect(url_for('actualizacion_datos', direccion_guardada="1"))


@app.route('/borrar_direccion/<int:id_direccion>', methods=['POST'])
def borrar_direccion(id_direccion):
    direccion = Direccion.query.get_or_404(id_direccion)
    db.session.delete(direccion)
    db.session.commit()
    flash("Dirección eliminada correctamente 🗑️", "success")
    return redirect(url_for('actualizacion_datos', direccion_eliminada=1))




@app.route('/notificaciones', methods=['GET', 'POST'])
def ver_notificaciones():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for('login'))

    if request.method == 'POST':
        ids = request.form.getlist('ids')
        if ids:
            Notificaciones.query.filter(
                Notificaciones.ID_Usuario == user_id,
                Notificaciones.ID_Notificacion.in_(ids)
            ).delete(synchronize_session=False)
            db.session.commit()
            flash("✅ Notificaciones eliminadas", "success")
        return redirect(url_for('ver_notificaciones'))

    notificaciones = Notificaciones.query.filter_by(ID_Usuario=user_id).order_by(Notificaciones.Fecha.desc()).all()
    return render_template("notificaciones.html", notificaciones=notificaciones)




@app.route('/eliminar_notificaciones', methods=['POST'])
def eliminar_notificaciones():
    user_id = session.get("user_id")
    if not user_id:
        return {"status": "error", "message": "No autorizado"}, 401

    ids = request.json.get("ids", [])
    if not ids:
        return {"status": "error", "message": "No seleccionaste ninguna notificación"}, 400

    try:
        Notificaciones.query.filter(
            Notificaciones.ID_Notificacion.in_(ids),
            Notificaciones.ID_Usuario == user_id
        ).delete(synchronize_session=False)
        db.session.commit()
        return {"status": "success", "message": "Notificaciones eliminadas correctamente"}
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": f"Error al eliminar: {str(e)}"}, 500

# En tu app.py
def crear_notificacion(user_id, titulo, mensaje):
    """Crea y guarda una notificación real para un usuario"""
    noti = Notificaciones(
        ID_Usuario=user_id,
        Titulo=titulo,
        Mensaje=mensaje
    )
    db.session.add(noti)
    db.session.commit()



if __name__ == '__main__':
    app.run(debug=True)
