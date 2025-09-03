"""
Módulo Chatbot para Casa en el Árbol
====================================

Este módulo contiene toda la lógica del chatbot incluyendo:
- Base de conocimientos (knowledge_base.py)
- Manejador de respuestas (response_handler.py) 
- Gestor de sesiones (session_manager.py)

Autor: Casa en el Árbol
Versión: 1.0.0
"""

from .knowledge_base import ChatbotKnowledge
from .response_handler import ResponseHandler
from .session_manager import SessionManager

__version__ = '1.0.0'
__author__ = 'Casa en el Árbol'

__all__ = [
    'ChatbotKnowledge',
    'ResponseHandler', 
    'SessionManager'
]