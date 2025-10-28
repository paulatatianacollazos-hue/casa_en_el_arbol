from flask import Blueprint, render_template
from flask_login import login_required
from basedatos.decoradores import role_required

empleado = Blueprint('empleado', __name__, url_prefix='/empleado')


@empleado.route('/dashboard')
@login_required
@role_required('instalador', 'transportista')
def dashboard():
    return render_template('empleado/dashboard.html')
