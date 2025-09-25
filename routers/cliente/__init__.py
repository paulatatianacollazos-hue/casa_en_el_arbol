from flask import Blueprint

cliente = Blueprint('cliente', __name__, template_folder='templates')


from . import routes
