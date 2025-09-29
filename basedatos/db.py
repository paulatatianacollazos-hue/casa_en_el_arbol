# basedatos/db.py 2426
import mysql.connector

def get_connection():
    """Devuelve una conexión nueva a la base de datos."""
    return mysql.connector.connect(
        user='root',
        password='paula123',
        host='localhost',
        database='tienda_db',
    )
