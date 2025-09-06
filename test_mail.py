from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)

# --- Configuración del correo ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'nataliamelendez2426@gmail.com'       # ⚡ tu correo Gmail válido
app.config['MAIL_PASSWORD'] = 'Natalia2426'         # ⚡ contraseña de aplicación (16 caracteres)
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

mail = Mail(app)

@app.route('/send_test')
def send_test():
    try:
        msg = Message(
            subject="Prueba Flask-Mail",          
            recipients=["natalia2426@gmail.com"],  # ⚡ cambia por el correo de destino
            body="Este es un correo de prueba enviado desde Flask con UTF-8."
        )
        mail.send(msg)
        return "✅ Correo de prueba enviado con éxito"
    except Exception as e:
        return f"❌ Error al enviar correo: {e}"

if __name__ == '__main__':
    app.run(debug=True)
