from flask import session, request
from datetime import datetime

def registrar_historial(tipo, descripcion, icono):
    if 'historial' not in session:
        session['historial'] = []

    actividad = {
        "tipo": tipo,
        "descripcion": descripcion,
        "icono": icono,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "ubicacion": "Bogotá, Colombia",
        "navegador": request.user_agent.browser or "Desconocido"
    }

    session['historial'].append(actividad)
    session.modified = True
