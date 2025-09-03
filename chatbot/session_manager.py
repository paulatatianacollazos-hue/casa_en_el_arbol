import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import threading
import time

class SessionManager:
    """Manejador de sesiones del chatbot"""
    
    def __init__(self):
        self.sessions = {}
        self.session_lock = threading.Lock()
        
        # Configuración
        self.max_session_duration = timedelta(hours=2)  # Sesiones expiran en 2 horas
        self.max_messages_per_session = 500
        
        # Iniciar limpieza automática de sesiones
        self._start_cleanup_thread()
    
    def create_session(self, session_id: str) -> Dict[str, Any]:
        """Crear nueva sesión de chat"""
        with self.session_lock:
            session_data = {
                'session_id': session_id,
                'created_at': datetime.now(),
                'last_activity': datetime.now(),
                'messages': [],
                'user_info': {},
                'context': {},
                'message_count': 0,
                'is_active': True
            }
            
            self.sessions[session_id] = session_data
            return session_data
    
    def add_message(self, session_id: str, message: str, sender: str) -> bool:
        """Agregar mensaje a la sesión"""
        with self.session_lock:
            if session_id not in self.sessions:
                self.create_session(session_id)
            
            session = self.sessions[session_id]
            
            # Verificar límites
            if session['message_count'] >= self.max_messages_per_session:
                return False
            
            # Agregar mensaje
            message_data = {
                'message': message,
                'sender': sender,
                'timestamp': datetime.now(),
                'formatted_time': datetime.now().strftime('%H:%M')
            }
            
            session['messages'].append(message_data)
            session['last_activity'] = datetime.now()
            session['message_count'] += 1
            
            return True
    
    def get_session_history(self, session_id: str) -> List[Dict]:
        """Obtener historial de mensajes de una sesión"""
        with self.session_lock:
            if session_id not in self.sessions:
                return []
            
            return [
                {
                    'message': msg['message'],
                    'sender': msg['sender'],
                    'timestamp': msg['timestamp'].isoformat(),
                    'formatted_time': msg['formatted_time']
                }
                for msg in self.sessions[session_id]['messages']
            ]
    
    def update_session_context(self, session_id: str, context_key: str, context_value: Any):
        """Actualizar contexto de la sesión"""
        with self.session_lock:
            if session_id in self.sessions:
                self.sessions[session_id]['context'][context_key] = context_value
                self.sessions[session_id]['last_activity'] = datetime.now()
    
    def get_session_context(self, session_id: str) -> Dict:
        """Obtener contexto de la sesión"""
        with self.session_lock:
            if session_id not in self.sessions:
                return {}
            return self.sessions[session_id]['context'].copy()
    
    def update_user_info(self, session_id: str, user_data: Dict):
        """Actualizar información del usuario"""
        with self.session_lock:
            if session_id in self.sessions:
                self.sessions[session_id]['user_info'].update(user_data)
                self.sessions[session_id]['last_activity'] = datetime.now()
    
    def get_user_info(self, session_id: str) -> Dict:
        """Obtener información del usuario"""
        with self.session_lock:
            if session_id not in self.sessions:
                return {}
            return self.sessions[session_id]['user_info'].copy()
    
    def is_session_active(self, session_id: str) -> bool:
        """Verificar si una sesión está activa"""
        with self.session_lock:
            if session_id not in self.sessions:
                return False
            
            session = self.sessions[session_id]
            time_since_activity = datetime.now() - session['last_activity']
            
            return (session['is_active'] and 
                   time_since_activity < self.max_session_duration)
    
    def clear_session_history(self, session_id: str):
        """Limpiar historial de mensajes de una sesión"""
        with self.session_lock:
            if session_id in self.sessions:
                self.sessions[session_id]['messages'] = []
                self.sessions[session_id]['message_count'] = 0
                self.sessions[session_id]['context'] = {}
                self.sessions[session_id]['last_activity'] = datetime.now()
    
    def remove_session(self, session_id: str):
        """Eliminar sesión completamente"""
        with self.session_lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
    
    def get_session_stats(self, session_id: str) -> Dict:
        """Obtener estadísticas de la sesión"""
        with self.session_lock:
            if session_id not in self.sessions:
                return {}
            
            session = self.sessions[session_id]
            user_messages = [msg for msg in session['messages'] if msg['sender'] == 'user']
            bot_messages = [msg for msg in session['messages'] if msg['sender'] == 'bot']
            
            return {
                'total_messages': len(session['messages']),
                'user_messages': len(user_messages),
                'bot_messages': len(bot_messages),
                'session_duration': (datetime.now() - session['created_at']).total_seconds() / 60,  # en minutos
                'last_activity': session['last_activity'].isoformat(),
                'is_active': self.is_session_active(session_id)
            }
    
    def get_all_active_sessions(self) -> List[str]:
        """Obtener lista de sesiones activas"""
        with self.session_lock:
            active_sessions = []
            for session_id, session in self.sessions.items():
                if self.is_session_active(session_id):
                    active_sessions.append(session_id)
            return active_sessions
    
    def export_session_data(self, session_id: str) -> Dict:
        """Exportar datos de la sesión para análisis"""
        with self.session_lock:
            if session_id not in self.sessions:
                return {}
            
            session = self.sessions[session_id]
            
            return {
                'session_info': {
                    'session_id': session_id,
                    'created_at': session['created_at'].isoformat(),
                    'last_activity': session['last_activity'].isoformat(),
                    'message_count': session['message_count']
                },
                'messages': [
                    {
                        'message': msg['message'],
                        'sender': msg['sender'],
                        'timestamp': msg['timestamp'].isoformat()
                    }
                    for msg in session['messages']
                ],
                'user_info': session['user_info'],
                'context': session['context']
            }
    
    def _cleanup_expired_sessions(self):
        """Limpiar sesiones expiradas"""
        with self.session_lock:
            expired_sessions = []
            now = datetime.now()
            
            for session_id, session in self.sessions.items():
                time_since_activity = now - session['last_activity']
                if time_since_activity > self.max_session_duration:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.sessions[session_id]
                print(f"Sesión expirada eliminada: {session_id}")
    
    def _start_cleanup_thread(self):
        """Iniciar hilo de limpieza automática"""
        def cleanup_loop():
            while True:
                time.sleep(1800)  # Limpiar cada 30 minutos
                self._cleanup_expired_sessions()
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
    
    def get_system_stats(self) -> Dict:
        """Obtener estadísticas del sistema"""
        with self.session_lock:
            active_count = len(self.get_all_active_sessions())
            total_sessions = len(self.sessions)
            
            total_messages = sum(len(session['messages']) for session in self.sessions.values())
            
            return {
                'active_sessions': active_count,
                'total_sessions': total_sessions,
                'total_messages': total_messages,
                'average_messages_per_session': total_messages / max(total_sessions, 1),
                'timestamp': datetime.now().isoformat()
            }