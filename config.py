import os
from datetime import timedelta

class Config:
    """Configuración base de la aplicación"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'casa_en_el_arbol_secret_2024_super_secure'
    
    # Configuración de Socket.IO
    SOCKETIO_ASYNC_MODE = 'eventlet'
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    SOCKETIO_PING_TIMEOUT = 60
    SOCKETIO_PING_INTERVAL = 25
    
    # Configuración del chatbot
    CHATBOT_MAX_SESSIONS = 1000
    CHATBOT_SESSION_TIMEOUT = timedelta(hours=2)
    CHATBOT_MAX_MESSAGES_PER_SESSION = 500
    CHATBOT_RESPONSE_DELAY = (0.5, 2.0)  # Min, Max segundos
    
    # Configuración de logs
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configuración de la empresa
    COMPANY_INFO = {
        'name': 'Casa en el Árbol',
        'slogan': 'Muebles únicos para tu hogar',
        'email': 'info@casaenelarbol.com',
        'phone': '+57 300 123 4567',
        'address': 'Calle 123 #45-67, Barrio Los Pinos, Bogotá',
        'business_hours': 'Lunes a Viernes: 8:00 AM - 6:00 PM, Sábados: 9:00 AM - 4:00 PM'
    }

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False
    
    # Configuración más relajada para desarrollo
    CHATBOT_RESPONSE_DELAY = (0.2, 1.0)
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False
    
    # Configuración más estricta para producción
    SOCKETIO_CORS_ALLOWED_ORIGINS = ["https://casaenelarbol.com", "https://www.casaenelarbol.com"]
    CHATBOT_MAX_SESSIONS = 500
    
    # Usar variable de entorno para la clave secreta
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("No se encontró SECRET_KEY en las variables de entorno")

class TestingConfig(Config):
    """Configuración para testing"""
    DEBUG = True
    TESTING = True
    CHATBOT_RESPONSE_DELAY = (0.1, 0.3)

# Mapeo de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}