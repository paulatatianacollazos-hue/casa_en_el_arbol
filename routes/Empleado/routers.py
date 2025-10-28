from flask import Blueprint, render_template

empleado = Blueprint('empleado', __name__)


@empleado.route('/dashboard')
@empleado.route('/instalador')
@empleado.route('/transportista')
def instalador_dashboard():
    return render_template('dashboards/dashboard.html')
