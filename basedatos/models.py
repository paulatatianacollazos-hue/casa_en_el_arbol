from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class Usuario(UserMixin, db.Model):
    __tablename__ = 'Usuario'

    ID_Usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Nombre = db.Column(db.String(100), nullable=False)
    Apellido = db.Column(db.String(100))
    Genero = db.Column(db.String(10))
    Telefono = db.Column(db.String(20))
    Correo = db.Column(db.String(100), nullable=False, unique=True)
    Contraseña = db.Column(db.String(200), nullable=False)
    Rol = db.Column(db.String(50), default='cliente')
    Activo = db.Column(db.Boolean, default=True)

    # Relaciones
    calendarios = db.relationship('Calendario', backref='usuario', lazy=True)
    notificaciones = db.relationship('Notificaciones', backref='usuario', lazy=True)
    novedades = db.relationship('Novedades', backref='usuario', lazy=True)
    pedidos = db.relationship('Pedido', backref='usuario', lazy=True)
    direcciones = db.relationship('Direccion', backref='usuario', lazy=True, cascade="all, delete-orphan")

    # ✅ Esto ya está bien
    def get_id(self):
        return str(self.ID_Usuario)

    # ✅ Agrega esto para compatibilidad con current_user.id
    @property
    def id(self):
        return self.ID_Usuario

    def __repr__(self):
        return f'<Usuario {self.Nombre} {self.Apellido or ""}>'



class Direccion(db.Model):
    __tablename__ = 'Direccion'

    ID_Direccion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ID_Usuario = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'), nullable=False)
    Pais = db.Column(db.String(100), default="Colombia")
    Departamento = db.Column(db.String(100))
    Ciudad = db.Column(db.String(100))
    Direccion = db.Column(db.String(200), nullable=False)
    InfoAdicional = db.Column(db.String(200))
    Barrio = db.Column(db.String(100))
    Destinatario = db.Column(db.String(100))

    def __repr__(self):
        return f'<Direccion {self.Direccion}, {self.Ciudad}>'


class Proveedor(db.Model):
    __tablename__ = 'Proveedor'

    ID_Proveedor = db.Column(db.Integer, primary_key=True, autoincrement=True)
    NombreEmpresa = db.Column(db.String(100), nullable=False)
    NombreContacto = db.Column(db.String(100))
    Telefono = db.Column(db.String(20))
    Pais = db.Column(db.String(50))
    CargoContacto = db.Column(db.String(50))

    # Relaciones
    productos = db.relationship('Producto', backref='proveedor', lazy=True)

    def __repr__(self):
        return f'<Proveedor {self.NombreEmpresa}>'


class Categorias(db.Model):
    __tablename__ = 'Categorias'

    ID_Categoria = db.Column(db.Integer, primary_key=True, autoincrement=True)
    NombreCategoria = db.Column(db.String(100), nullable=False)
    Descripcion = db.Column(db.Text)

    # Relaciones
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

    # Claves foráneas
    ID_Categoria = db.Column(db.Integer, db.ForeignKey('Categorias.ID_Categoria'), nullable=False)
    ID_Proveedor = db.Column(db.Integer, db.ForeignKey('Proveedor.ID_Proveedor'), nullable=False)

    # Relaciones
    detalles_pedido = db.relationship('Detalle_Pedido', backref='producto', lazy=True)
    novedades = db.relationship('Novedades', backref='producto', lazy=True)

    def __repr__(self):
        return f'<Producto {self.NombreProducto}>'


class Calendario(db.Model):
    __tablename__ = 'Calendario'

    ID_Calendario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Fecha = db.Column(db.Date)
    Hora = db.Column(db.Time)
    Ubicacion = db.Column(db.String(200))

    # Clave foránea
    ID_Usuario = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'), nullable=False)

    def __repr__(self):
        return f'<Calendario {self.ID_Calendario}>'


class Notificaciones(db.Model):
    __tablename__ = 'Notificaciones'

    ID_Notificacion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Titulo = db.Column(db.String(200), nullable=False)
    Mensaje = db.Column(db.Text, nullable=False)
    Fecha = db.Column(db.DateTime, default=db.func.current_timestamp())
    Leida = db.Column(db.Boolean, default=False)

    # Clave foránea
    ID_Usuario = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'), nullable=False)

    def __repr__(self):
        return f"<Notificacion {self.Titulo}>"


class Novedades(db.Model):
    __tablename__ = 'Novedades'

    ID_Novedad = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Tipo = db.Column(db.String(50))
    EstadoNovedad = db.Column(db.String(50))
    FechaReporte = db.Column(db.Date)

    # Claves foráneas
    ID_Usuario = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'), nullable=False)
    ID_Producto = db.Column(db.Integer, db.ForeignKey('Producto.ID_Producto'), nullable=False)

    def __repr__(self):
        return f'<Novedad {self.ID_Novedad}>'


class Pedido(db.Model):
    __tablename__ = 'Pedido'

    ID_Pedido = db.Column(db.Integer, primary_key=True, autoincrement=True)
    NombreComprador = db.Column(db.String(100))
    Estado = db.Column(db.String(50))
    FechaPedido = db.Column(db.Date)
    FechaEntrega = db.Column(db.Date)
    Destino = db.Column(db.String(200))
    Descuento = db.Column(db.Float)

    # Clave foránea
    ID_Usuario = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'), nullable=False)

    # Relaciones
    pagos = db.relationship('Pagos', backref='pedido', lazy=True)
    detalles_pedido = db.relationship('Detalle_Pedido', backref='pedido', lazy=True)

    def __repr__(self):
        return f'<Pedido {self.ID_Pedido}>'


class Pagos(db.Model):
    __tablename__ = 'Pagos'

    ID_Pagos = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MetodoPago = db.Column(db.String(50))
    FechaPago = db.Column(db.Date)
    Monto = db.Column(db.Float)

    # Clave foránea
    ID_Pedido = db.Column(db.Integer, db.ForeignKey('Pedido.ID_Pedido'), nullable=False)

    def __repr__(self):
        return f'<Pago {self.ID_Pagos}>'


class Detalle_Pedido(db.Model):
    __tablename__ = 'Detalle_Pedido'

    ID_Pedido = db.Column(db.Integer, db.ForeignKey('Pedido.ID_Pedido'), primary_key=True)
    ID_Producto = db.Column(db.Integer, db.ForeignKey('Producto.ID_Producto'), primary_key=True)
    Cantidad = db.Column(db.Integer)
    PrecioUnidad = db.Column(db.Float)

    def __repr__(self):
        return f'<Detalle_Pedido Pedido: {self.ID_Pedido}, Producto: {self.ID_Producto}>'
