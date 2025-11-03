from flask import current_app, Blueprint, render_template
from basedatos.decoradores import role_required

empleado = Blueprint(
    'empleado',
    __name__,
    template_folder='templates',
    url_prefix='/empleado'
)


@empleado.route('/dashboard')
@role_required("transportista")
def dashboard():
    return render_template('empleado/dashboard.html')


@empleado.route('/calendario')
@role_required("transportista")
def calendario():
    return render_template('empleado/calendario.html')
