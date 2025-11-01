from flask import Blueprint

empleado = Blueprint(
    'empleado',
    __name__,
    template_folder='templates',
    url_prefix='/empleado'  # mejor mantener minúsculas y coherente
)

from . import routes
