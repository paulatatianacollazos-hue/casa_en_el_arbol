from flask import Blueprint, render_template
from flask_login import login_required
from basedatos.decoradores import role_required

# 🔸 Creamos el Blueprint con el nombre correcto
empleado = Blueprint('empleado', __name__, url_prefix='/empleado')


@empleado.route('/dadashboard')
@login_required
def dashboard():
    return render_template('empleado/dashboard.html')
