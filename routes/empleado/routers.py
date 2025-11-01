from flask import current_app, Blueprint, render_template

empleado = Blueprint(
    'empleado',
    __name__,
    template_folder='templates',
    url_prefix='/empleado'
)


@empleado.route('/dashboard')
def dashboard_empleado():
    return render_template('empleado/dashboard.html')
