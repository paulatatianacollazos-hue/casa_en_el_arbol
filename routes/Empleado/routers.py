from flask import Blueprint, render_template
from flask_login import login_required
from basedatos.decoradores import role_required

# 🔸 Creamos el Blueprint con el nombre correcto
empleado = Blueprint('empleado', __name__, url_prefix='/empleado')


@empleado.route('/dadashboard')
@login_required
@role_required('instalador, transportista')
def dashboard():
    return render_template('empleado/dashboard.html')


# ---------- DASHBOARDS EMPLEADO ----------
@empleado.route('/instalador')
@login_required
@role_required('instalador')
def instalador_dashboard():
    return render_template('empleado/dashboard.html')


@empleado.route('/transportista')
@login_required
@role_required('transportista')
def transportista_dashboard():
    return render_template('empleado/dashboard.html')
