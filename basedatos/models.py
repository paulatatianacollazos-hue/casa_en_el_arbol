import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Usuario(db.Model):
    __tablename__ = 'Usuario'
    ID_Usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Nombre = db.Column(db.String(100), nullable=False)
    Telefono = db.Column(db.String(20))
    Correo = db.Column(db.String(100), unique=True, nullable=False)
    Direccion = db.Column(db.String(200))
    Contrasena = db.Column(db.String(200), nullable=False)  # corregido sin ñ
    Rol = db.Column(db.String(50), default='cliente')
    Activo = db.Column(db.Boolean, default=True)

    calendarios = db.relationship('Calendario', backref='usuario', lazy=True)
    notificaciones = db.relationship('Notificacion', backref='usuario', lazy=True)
    novedades = db.relationship('Novedad', backref='usuario', lazy=True)
    pedidos = db.relationship('Pedido', backref='usuario', lazy=True)

    def __repr__(self):
        return f'<Usuario {self.Nombre}>'


class Proveedor(db.Model):
    __tablename__ = 'Proveedor'
    ID_Proveedor = db.Column(db.Integer, primary_key=True, autoincrement=True)
    NombreEmpresa = db.Column(db.String(100), nullable=False)
    NombreContacto = db.Column(db.String(100))
    Telefono = db.Column(db.String(20))
    Pais = db.Column(db.String(50))
    CargoContacto = db.Column(db.String(50))

    productos = db.relationship('Producto', backref='proveedor', lazy=True)

    def __repr__(self):
        return f'<Proveedor {self.NombreEmpresa}>'


class Categoria(db.Model):
    __tablename__ = 'Categoria'
    ID_Categoria = db.Column(db.Integer, primary_key=True, autoincrement=True)
    NombreCategoria = db.Column(db.String(100), nullable=False)
    Descripcion = db.Column(db.Text)

    productos = db.relationship('Producto', backref='categoria', lazy=True)

    def __repr__(self):
        return f'<Categoria {self.NombreCategoria}>'


class Producto(db.Model):
    __tablename__ = 'Producto'
    ID_Producto = db.Column(db.Integer, primary_key=True, autoincrement=True)
    NombreProducto = db.Column(db.String(100), nullable=False)
    Stock = db.Column(db.Integer)
    Material = db.Column(db.String(50))
    Color = db.Column(db.String(30))
    PrecioUnidad = db.Column(db.Float)

    ID_Categoria = db.Column(db.Integer, db.ForeignKey('Categoria.ID_Categoria'), nullable=False)
    ID_Proveedor = db.Column(db.Integer, db.ForeignKey('Proveedor.ID_Proveedor'), nullable=False)

    detalles_pedido = db.relationship('Detalle_Pedido', backref='producto', lazy=True)
    novedades = db.relationship('Novedad', backref='producto', lazy=True)

    def __repr__(self):
        return f'<Producto {self.NombreProducto}>'


class Calendario(db.Model):
    __tablename__ = 'Calendario'
    ID_Calendario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Fecha = db.Column(db.DateTime, default=datetime.utcnow)
    Ubicacion = db.Column(db.String(200))

    ID_Usuario = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'), nullable=False)

    def __repr__(self):
        return f'<Calendario {self.ID_Calendario}>'


class Notificacion(db.Model):
    __tablename__ = 'Notificacion'
    ID_Notificacion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Fecha = db.Column(db.DateTime, default=datetime.utcnow)
    Mensaje = db.Column(db.Text)

    ID_Usuario = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'), nullable=False)

    def __repr__(self):
        return f'<Notificacion {self.ID_Notificacion}>'


class Novedad(db.Model):
    __tablename__ = 'Novedad'
    ID_Novedad = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Tipo = db.Column(db.String(50))
    EstadoNovedad = db.Column(db.String(50))
    FechaReporte = db.Column(db.DateTime, default=datetime.utcnow)

    ID_Usuario = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'), nullable=False)
    ID_Producto = db.Column(db.Integer, db.ForeignKey('Producto.ID_Producto'), nullable=False)

    def __repr__(self):
        return f'<Novedad {self.ID_Novedad}>'


class Pedido(db.Model):
    __tablename__ = 'Pedido'
    ID_Pedido = db.Column(db.Integer, primary_key=True, autoincrement=True)
    NombreComprador = db.Column(db.String(100))
    Estado = db.Column(db.String(50))
    FechaPedido = db.Column(db.DateTime, default=datetime.utcnow)
    FechaEntrega = db.Column(db.DateTime)
    Destino = db.Column(db.String(200))
    Descuento = db.Column(db.Float)

    ID_Usuario = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'), nullable=False)

    pagos = db.relationship('Pago', backref='pedido', lazy=True)
    detalles_pedido = db.relationship('Detalle_Pedido', backref='pedido', lazy=True)

    def __repr__(self):
        return f'<Pedido {self.ID_Pedido}>'


class Pago(db.Model):
    __tablename__ = 'Pago'
    ID_Pago = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MetodoPago = db.Column(db.String(50))
    FechaPago = db.Column(db.DateTime, default=datetime.utcnow)
    Monto = db.Column(db.Float)

    ID_Pedido = db.Column(db.Integer, db.ForeignKey('Pedido.ID_Pedido'), nullable=False)

    def __repr__(self):
        return f'<Pago {self.ID_Pago}>'


class Detalle_Pedido(db.Model):
    __tablename__ = 'Detalle_Pedido'
    ID_Pedido = db.Column(db.Integer, db.ForeignKey('Pedido.ID_Pedido'), primary_key=True)
    ID_Producto = db.Column(db.Integer, db.ForeignKey('Producto.ID_Producto'), primary_key=True)
    Cantidad = db.Column(db.Integer)
    PrecioUnidad = db.Column(db.Float)

    def __repr__(self):
        return f'<Detalle_Pedido Pedido: {self.ID_Pedido}, Producto: {self.ID_Producto}>'
