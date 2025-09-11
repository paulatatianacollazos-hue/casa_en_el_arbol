import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from basedatos.models import db, Usuario

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
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password', '').strip()

        if not name or not email or not password:
            flash('Completa todos los campos')
            return render_template('register.html')

        try:
            if Usuario.query.filter_by(Correo=email).first():
                flash('Correo ya registrado')
                return render_template('register.html')

            hashed_password = generate_password_hash(password)
            user = Usuario(Nombre=name, Correo=email, Telefono=phone,
                           Contraseña=hashed_password, Rol='cliente', Activo=True)
            db.session.add(user)
            db.session.commit()

            flash('Cuenta creada. ¡Ahora inicia sesión!')
            return redirect(url_for('login'))

        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Error al registrar: {str(e)}')
            return render_template('register.html')
        

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
    session.pop('usuario', None)
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
    






if __name__ == '__main__':
    app.run(debug=True)
