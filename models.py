from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'Usuario'

    ID_Usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Nombre = db.Column(db.String(100), nullable=False)
    Telefono = db.Column(db.String(20), default=None)
    Correo = db.Column(db.String(100), unique=True, nullable=False)
    Direccion = db.Column(db.String(200), default=None)
    Contrasena = db.Column(db.String(255), nullable=False)
    Rol = db.Column(db.String(50), default="cliente", server_default="cliente")
    Activo = db.Column(db.Boolean, default=True, server_default="1")

    calendarios = db.relationship("Calendario", back_populates="usuario", lazy='dynamic', cascade="all, delete-orphan")
    notificaciones = db.relationship("Notificaciones", back_populates="usuario", lazy='dynamic', cascade="all, delete-orphan")
    pedidos = db.relationship("Pedido", back_populates="usuario", lazy='dynamic', cascade="all, delete-orphan")
    novedades = db.relationship("Novedades", back_populates="usuario", lazy='dynamic', cascade="all, delete-orphan")

    def _repr_(self):
        return f"<Usuario(id={self.ID_Usuario}, nombre='{self.Nombre}', correo='{self.Correo}')>"


class Proveedor(db.Model):
    __tablename__ = 'Proveedor'

    ID_Proveedor = db.Column(db.Integer, primary_key=True, autoincrement=True)
    NombreEmpresa = db.Column(db.String(100), nullable=False)
    NombreContacto = db.Column(db.String(100), nullable=False)
    Telefono = db.Column(db.String(20), default=None)
    Pais = db.Column(db.String(50), default=None)
    CargoContacto = db.Column(db.String(50), default=None)

    productos = db.relationship("Producto", back_populates="proveedor", lazy='dynamic')

    def _repr_(self):
        return f"<Proveedor(id={self.ID_Proveedor}, empresa='{self.NombreEmpresa}')>"


class Categorias(db.Model):
    __tablename__ = 'Categorias'

    ID_Categoria = db.Column(db.Integer, primary_key=True, autoincrement=True)
    NombreCategoria = db.Column(db.String(100), nullable=False)
    Descripcion = db.Column(db.Text, default=None)

    productos = db.relationship("Producto", back_populates="categoria", lazy='dynamic')

    def _repr_(self):
        return f"<Categoria(id={self.ID_Categoria}, nombre='{self.NombreCategoria}')>"


class Calendario(db.Model):
    __tablename__ = 'Calendario'

    ID_Calendario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Fecha = db.Column(db.Date, default=datetime.utcnow, nullable=False)
    Hora = db.Column(db.Time, default=None)
    Ubicacion = db.Column(db.String(200), default=None)
    ID_Usuario = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'), nullable=False)

    usuario = db.relationship("Usuario", back_populates="calendarios")

    def _repr_(self):
        return f"<Calendario(id={self.ID_Calendario}, fecha='{self.Fecha}')>"


class Notificaciones(db.Model):
    __tablename__ = 'Notificaciones'

    ID_Notificacion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Fecha = db.Column(db.Date, default=datetime.utcnow, nullable=False)
    Mensaje = db.Column(db.Text, nullable=False)
    ID_Usuario = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'), nullable=False)

    usuario = db.relationship("Usuario", back_populates="notificaciones")

    def _repr_(self):
        return f"<Notificacion(id={self.ID_Notificacion})>"


class Producto(db.Model):
    __tablename__ = 'Producto'

    ID_Producto = db.Column(db.Integer, primary_key=True, autoincrement=True)
    NombreProducto = db.Column(db.String(100), nullable=False)
    Stock = db.Column(db.Integer, default=0)
    Material = db.Column(db.String(50), default=None)
    Color = db.Column(db.String(30), default=None)
    PrecioUnidad = db.Column(db.Float, nullable=False)
    ID_Categoria = db.Column(db.Integer, db.ForeignKey('Categorias.ID_Categoria'), nullable=False)
    ID_Proveedor = db.Column(db.Integer, db.ForeignKey('Proveedor.ID_Proveedor'), nullable=False)

    categoria = db.relationship("Categorias", back_populates="productos")
    proveedor = db.relationship("Proveedor", back_populates="productos")
    novedades = db.relationship("Novedades", back_populates="producto", lazy='dynamic')
    detalles_pedido = db.relationship("DetallePedido", back_populates="producto", lazy='dynamic')

    def _repr_(self):
        return f"<Producto(id={self.ID_Producto}, nombre='{self.NombreProducto}')>"


class Novedades(db.Model):
    __tablename__ = 'Novedades'

    ID_Novedad = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Tipo = db.Column(db.String(50), nullable=False)
    EstadoNovedad = db.Column(db.String(50), default="abierta")
    FechaReporte = db.Column(db.Date, default=datetime.utcnow, nullable=False)
    ID_Usuario = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'), nullable=False)
    ID_Producto = db.Column(db.Integer, db.ForeignKey('Producto.ID_Producto'), nullable=False)

    usuario = db.relationship("Usuario", back_populates="novedades")
    producto = db.relationship("Producto", back_populates="novedades")

    def _repr_(self):
        return f"<Novedad(id={self.ID_Novedad}, tipo='{self.Tipo}')>"


class Pedido(db.Model):
    __tablename__ = 'Pedido'

    ID_Pedido = db.Column(db.Integer, primary_key=True, autoincrement=True)
    NombreComprador = db.Column(db.String(100), nullable=False)
    Estado = db.Column(db.String(50), default="pendiente")
    FechaPedido = db.Column(db.Date, default=datetime.utcnow, nullable=False)
    FechaEntrega = db.Column(db.Date, default=None)
    Destino = db.Column(db.String(200), nullable=False)
    Descuento = db.Column(db.Float, default=0.0)
    ID_Usuario = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'), nullable=False)

    usuario = db.relationship("Usuario", back_populates="pedidos")
    pagos = db.relationship("Pagos", back_populates="pedido", lazy='dynamic')
    detalles_pedido = db.relationship("DetallePedido", back_populates="pedido", lazy='dynamic', cascade="all, delete-orphan")

    def _repr_(self):
        return f"<Pedido(id={self.ID_Pedido}, estado='{self.Estado}')>"


class Pagos(db.Model):
    __tablename__ = 'Pagos'

    ID_Pagos = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MetodoPago = db.Column(db.String(50), nullable=False)
    FechaPago = db.Column(db.Date, default=datetime.utcnow, nullable=False)
    Monto = db.Column(db.Float, nullable=False)
    ID_Pedido = db.Column(db.Integer, db.ForeignKey('Pedido.ID_Pedido'), nullable=False)

    pedido = db.relationship("Pedido", back_populates="pagos")

    def _repr_(self):
        return f"<Pago(id={self.ID_Pagos}, monto='{self.Monto}')>"


class DetallePedido(db.Model):
    __tablename__= 'Detalle_Pedido'

    ID_Pedido = db.Column(db.Integer, db.ForeignKey('Pedido.ID_Pedido'), primary_key=True)
    ID_Producto = db.Column(db.Integer, db.ForeignKey('Producto.ID_Producto'), primary_key=True)
    Cantidad = db.Column(db.Integer, nullable=False)
    PrecioUnidad = db.Column(db.Float, nullable=False)

    pedido = db.relationship("Pedido", back_populates="detalles_pedido")
    producto = db.relationship("Producto", back_populates="detalles_pedido")

    def _repr_(self):
        return f"<DetallePedido(pedido_id={self.ID_Pedido}, producto_id={self.ID_Producto})>"