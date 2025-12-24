# extensions.py
from flask_mail import Mail
from flask_mysqldb import MySQL
from flask_sqlalchemy import SQLAlchemy

mail = Mail()
mysql = MySQL()
db = SQLAlchemy() 