from flask import Blueprint

cliente = Blueprint(
    'cliente',  # nombre del blueprint
    __name__,
    template_folder='templates',
    url_prefix='/cliente'
)

from . import routes  # importa tus rutas aquí
