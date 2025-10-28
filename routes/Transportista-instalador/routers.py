from flask import Blueprint, render_template

dashboards = Blueprint('dashboards', __name__)


@dashboards.route('/instalador_dashboard')
def instalador_dashboard():
    return render_template('dashboards/instalador_dashboard.html')
