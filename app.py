import os
import uuid
import pymysql
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from werkzeug.security import generate_password_hash, check_password_hash

# Chatbot y modelos
from basedatos.models import db, Usuario
from chatbot.knowledge_base import ChatbotKnowledge
from chatbot.response_handler import ResponseHandler
from chatbot.session_manager import SessionManager

import pymysql


# Importa el objeto 'db' y los modelos desde tu archivo de modelos
from basedatos.models import db, Usuario
from chatbot.knowledge_base import ChatbotKnowledge
from chatbot.response_handler import ResponseHandler
from chatbot.session_manager import SessionManager

# Configuración de la aplicación
app = Flask(__name__)

# Configuración de la base de datos MySQL en Laragon
DB_URL = 'mysql+pymysql://root:@127.0.0.1:3306/tienda_db'
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'clave_super_secreta'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}

# Inicializa la instancia de SQLAlchemy con la aplicación
db.init_app(app)

# Crea la base de datos y las tablas si no existen
with app.app_context():
    engine = create_engine(DB_URL)
    if not database_exists(engine.url):
        create_database(engine.url)
        print("Base de datos 'casaarbol' creada exitosamente.")
    db.create_all()
    print("Tablas de la base de datos creadas exitosamente.")

# --- RUTAS DE LA APLICACIÓN ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')

        if not name or not email or not password:
            flash('Por favor, completa todos los campos requeridos.')
            return render_template('register.html')

        try:
            existing_user = Usuario.query.filter_by(Correo=email).first()
            if existing_user:
                flash('El correo electrónico ya está registrado. Por favor, usa otro.')
                return render_template('register.html')

            hashed_password = generate_password_hash(password)
            
            new_user = Usuario(
                Nombre=name,
                Correo=email,
                Telefono=phone,
                Contraseña=hashed_password,
                Rol='cliente',
                Activo=True
            )
            
            print(f'Intentando agregar usuario: {new_user.Correo}')
            db.session.add(new_user)
            db.session.commit()

            flash('Cuenta creada exitosamente! Por favor, inicia sesión.')
            return redirect(url_for('login'))
        
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Ocurrió un error al intentar registrar el usuario: {str(e)}')
            return render_template('register.html')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Por favor, ingresa tu correo y contraseña.')
            return render_template('login.html')

        user = Usuario.query.filter_by(Correo=email).first()

        if user and check_password_hash(user.Contraseña, password):
            session['user_id'] = user.ID_Usuario
            session['username'] = user.Nombre
            flash('Has iniciado sesión con éxito!')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales inválidas. Por favor, revisa tu correo y contraseña.')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Has cerrado sesión.')
    return redirect(url_for('index'))

@app.route('/nosotros')
def nosotros():
    return render_template('Nosotros.html')


@app.route('/api/chat/init', methods=['POST'])
def init_chat():
    """Inicializar nueva sesión de chat"""
    session_id = str(uuid.uuid4())
    session_manager.create_session(session_id)
    
    return jsonify({
        'session_id': session_id,
        'welcome_message': {
            'text': '¡Hola! 👋 Soy tu asistente virtual de Casa en el Árbol. Estoy aquí para ayudarte con información sobre nuestros productos, precios, instalaciones y más. ¿En qué puedo ayudarte hoy?',
            'timestamp': datetime.now().isoformat(),
            'quick_replies': [
                '¿Cuáles son sus productos más populares?',
                '¿Hacen instalaciones?',
                '¿Tienen garantía?',
                '¿Cuáles son los precios?'
            ]
        }
    })

@socketio.on('connect')
def handle_connect():
    session_id = request.sid
    session_manager.create_session(session_id)
    print(f'Cliente conectado: {session_id}')
    
    # Enviar mensaje de bienvenida
    emit('bot_message', {
        'text': '¡Hola! 👋 Soy tu asistente virtual de Casa en el Árbol. Estoy aquí para ayudarte con información sobre nuestros productos, precios, instalaciones y más. ¿En qué puedo ayudarte hoy?',
        'timestamp': datetime.now().strftime('%H:%M'),
        'quick_replies': [
            '🏆 Productos populares',
            '🔧 Instalaciones', 
            '🛡️ Garantía',
            '💰 Precios'
        ]
    })

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.sid
    session_manager.remove_session(session_id)
    print(f'Cliente desconectado: {session_id}')

@socketio.on('user_message')
def handle_message(data):
    session_id = request.sid
    user_message = data['message']
    
    # Agregar mensaje del usuario a la sesión
    session_manager.add_message(session_id, user_message, 'user')
    
    # Mostrar indicador de escritura
    emit('typing_start')
    
    # Simular tiempo de procesamiento
    socketio.sleep(1)
    
    # Generar respuesta del bot
    bot_response = response_handler.generate_response(user_message, session_id)
    
    # Agregar respuesta del bot a la sesión
    session_manager.add_message(session_id, bot_response['text'], 'bot')
    
    # Enviar respuesta
    emit('typing_stop')
    emit('bot_message', {
        'text': bot_response['text'],
        'timestamp': datetime.now().strftime('%H:%M'),
        'suggestions': bot_response.get('suggestions', []),
        'quick_replies': bot_response.get('quick_replies', [])
    })

@socketio.on('quick_reply')
def handle_quick_reply(data):
    # Tratar las respuestas rápidas como mensajes normales
    handle_message({'message': data['reply']})

@app.route('/api/chat/history/<session_id>')
def get_chat_history(session_id):
    """Obtener historial de chat de una sesión"""
    history = session_manager.get_session_history(session_id)
    return jsonify(history)

@app.route('/api/chat/clear/<session_id>', methods=['POST'])
def clear_chat(session_id):
    """Limpiar historial de chat"""
    session_manager.clear_session_history(session_id)
    return jsonify({'status': 'success'})

@app.route('/api/products')
def get_products():
    """Endpoint para obtener información de productos"""
    return jsonify(knowledge.get_all_products())

@app.route('/api/services')
def get_services():
    """Endpoint para obtener información de servicios"""
    return jsonify(knowledge.get_all_services())

if __name__ == '__main__':
    # Crear carpetas necesarias si no existen
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('chatbot', exist_ok=True)
    
    # Ejecutar la aplicación
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    app.run(debug=True)
