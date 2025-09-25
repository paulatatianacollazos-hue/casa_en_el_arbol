from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from basedatos.models import db, Calendario  
from basedatos.decoradores import role_required
from datetime import datetime

instalaciones = Blueprint('instalaciones', __name__, url_prefix='/instalaciones')

# ---------- AGENDAR_INSTALACIONES ----------
@instalaciones.route('/', methods=['GET', 'POST'])
@login_required
def instalaciones_home():
    if request.method == 'POST':
        fecha = datetime.strptime(request.form['fecha'], "%Y-%m-%d").date()
        hora = datetime.strptime(request.form['hora'], "%H:%M").time()
        ubicacion = request.form['ubicacion']
        tipo = request.form.get('tipo', 'Instalación')

        nueva_cita = Calendario(
            Fecha=fecha,
            Hora=hora,
            Ubicacion=ubicacion,
            Tipo=tipo,
            ID_Usuario=current_user.ID_Usuario
        )

        db.session.add(nueva_cita)
        db.session.commit()

        flash("✅ Instalación agendada con éxito", "success")
        return redirect(url_for('instalaciones.confirmacion'))

    citas = Calendario.query.filter_by(ID_Usuario=current_user.ID_Usuario).all()
    return render_template("instalaciones.html", citas=citas)

# ----------CONFIRMACION_INSTALACIONES----------
@instalaciones.route('/confirmacion')
@login_required
def confirmacion():
    return render_template("confirmacion.html")

# ---------- LISTA_INSTALACIONES ----------

@instalaciones.route('/lista')
@login_required
def lista():
    citas = Calendario.query.filter_by(ID_Usuario=current_user.ID_Usuario).all()
    return render_template("lista.html", citas=citas)
