# basedatos/db.py
import mysql.connector


def get_connection():
    """Devuelve una conexión nueva a la base de datos."""
    return mysql.connector.connect(
        user='root',
        password='',
        host='localhost',
        database='tienda_db',
    )
