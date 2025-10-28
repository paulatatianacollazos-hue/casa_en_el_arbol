from flask import Blueprint, render_template

empleado = Blueprint('empleado', __name__)


@empleado.route('/dashboard')
def instalador_dashboard():
    return render_template('dashboards/dashboard.html')
