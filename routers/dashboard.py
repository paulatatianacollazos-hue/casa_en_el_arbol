from flask import Blueprint, render_template
from flask_login import login_required

from basedatos.decoradores import role_required


dashboards = Blueprint('dashboards', __name__, url_prefix='/dashboards')

# ---------- DASHBOARDS ----------
@dashboards.route('/admin')
@login_required
@role_required('admin')
def admin_dashboard():
    return render_template('administrador/admin_dashboard.html')

@dashboards.route('/cliente')
@login_required
@role_required('cliente')
def dashboard():
    return render_template('dashboard.html')

@dashboards.route('/instalador')
@login_required
@role_required('instalador')
def instalador_dashboard():
    return render_template('instalador_dashboard.html')

@dashboards.route('/transportista')
@login_required
@role_required('transportista')
def transportista_dashboard():
    return render_template('transportista_dashboard.html')
