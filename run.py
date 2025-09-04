#!/usr/bin/env python3
"""
Script de inicio para el chatbot de Casa en el Árbol
====================================================

Este script inicia la aplicación Flask con SocketIO en modo desarrollo.
Para producción, usar un servidor WSGI como Gunicorn.

Uso:
    python run.py [--port PORT] [--host HOST] [--debug]

Ejemplos:
    python run.py                    # Ejecutar en localhost:5000
    python run.py --port 8080        # Ejecutar en puerto 8080
    python run.py --host 0.0.0.0     # Permitir conexiones externas
    python run.py --debug            # Modo debug activado
"""

import argparse
import os
import sys
import logging
from datetime import datetime

# Agregar el directorio actual al path para importaciones
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, socketio
    from config import config
except ImportError as e:
    print(f"Error importando módulos: {e}")
    print("Asegúrate de que todos los archivos estén en su lugar y las dependencias instaladas.")
    sys.exit(1)

def setup_logging(debug=False):
    """Configurar logging de la aplicación"""
    level = logging.DEBUG if debug else logging.INFO
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'chatbot_{datetime.now().strftime("%Y%m%d")}.log')
        ]
    )
    
    # Configurar logs de Socket.IO
    socketio_logger = logging.getLogger('socketio')
    socketio_logger.setLevel(logging.WARNING if not debug else logging.DEBUG)

def check_dependencies():
    """Verificar que todas las dependencias estén instaladas"""
    required_modules = [
        'flask',
        'flask_socketio',
        'eventlet'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module.replace('_', '-'))
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("❌ Faltan dependencias:")
        for module in missing_modules:
            print(f"   - {module}")
        print("\n📦 Instala las dependencias con:")
        print("   pip install -r requirements.txt")
        return False
    
    print("✅ Todas las dependencias están instaladas")
    return True

def create_directories():
    """Crear directorios necesarios si no existen"""
    directories = [
        'templates',
        'static/css',
        'static/js', 
        'static/img',
        'chatbot',
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("📁 Directorios verificados/creados")

def print_startup_info(host, port, debug):
    """Mostrar información de inicio"""
    print("\n" + "="*60)
    print("🏡 CASA EN EL ÁRBOL - CHATBOT")
    print("="*60)
    print(f"🌐 Servidor: http://{host}:{port}")
    print(f"🔧 Modo debug: {'Activado' if debug else 'Desactivado'}")
    print(f"📊 WebSocket: Habilitado")
    print(f"⏰ Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print("📱 El chatbot estará disponible en la interfaz web")
    print("🔗 Endpoints API disponibles:")
    print("   - GET  /api/products     (Información de productos)")
    print("   - GET  /api/services     (Información de servicios)")
    print("   - POST /api/chat/init    (Inicializar sesión)")
    print("   - GET  /api/chat/history/<session_id> (Historial)")
    print("="*60)
    print("✨ ¡Listo para recibir conversaciones!")
    print("\n💡 Presiona Ctrl+C para detener el servidor\n")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Chatbot de Casa en el Árbol',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python run.py                     # Desarrollo local
  python run.py --port 8080         # Puerto personalizado
  python run.py --host 0.0.0.0      # Acceso desde otras máquinas
  python run.py --debug             # Modo debug
        """
    )
    
    parser.add_argument('--host', default='127.0.0.1', 
                       help='Host del servidor (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000,
                       help='Puerto del servidor (default: 5000)')
    parser.add_argument('--debug', action='store_true',
                       help='Activar modo debug')
    parser.add_argument('--config', default='development',
                       choices=['development', 'production', 'testing'],
                       help='Configuración a usar (default: development)')
    
    args = parser.parse_args()
    
    # Verificar dependencias
    if not check_dependencies():
        sys.exit(1)
    
    # Crear directorios necesarios
    create_directories()
    
    # Configurar logging
    setup_logging(args.debug)
    
    # Configurar la aplicación
    config_name = args.config
    app.config.from_object(config[config_name])
    
    # Mostrar información de inicio
    print_startup_info(args.host, args.port, args.debug)
    
    try:
        # Iniciar el servidor
        socketio.run(
            app,
            host=args.host,
            port=args.port,
            debug=args.debug,
            use_reloader=args.debug,
            log_output=args.debug
        )
    except KeyboardInterrupt:
        print("\n\n⏹️  Servidor detenido por el usuario")
        print("👋 ¡Gracias por usar el chatbot de Casa en el Árbol!")
    except Exception as e:
        print(f"\n❌ Error iniciando el servidor: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()