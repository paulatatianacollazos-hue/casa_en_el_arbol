from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


# ------------------ Usuario ------------------
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
    notificaciones = db.relationship('Notificaciones', backref='usuario',
                                     lazy=True)
    novedades = db.relationship('Novedades', backref='usuario', lazy=True)
    pedidos = db.relationship('Pedido', backref='usuario', lazy=True,
                              foreign_keys='Pedido.ID_Usuario')
    pedidos_asignados = db.relationship('Pedido', backref='empleado',
                                        lazy=True,
                                        foreign_keys='Pedido.ID_Empleado')
    direcciones = db.relationship('Direccion', backref='usuario',
                                  lazy=True, cascade="all, delete-orphan")

    def get_id(self):
        return str(self.ID_Usuario)

    @property
    def id(self):
        return self.ID_Usuario

    def __repr__(self):
        return f'<Usuario {self.Nombre} {self.Apellido or ""}>'


# ------------------ Direccion ------------------
class Direccion(db.Model):
    __tablename__ = 'Direccion'

    ID_Direccion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ID_Usuario = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario',
                                                     ondelete="CASCADE"),
                           nullable=False)
    Pais = db.Column(db.String(100), default="Colombia")
    Departamento = db.Column(db.String(100))
    Ciudad = db.Column(db.String(100))
    Direccion = db.Column(db.String(200), nullable=False)
    InfoAdicional = db.Column(db.String(200))
    Barrio = db.Column(db.String(100))
    Destinatario = db.Column(db.String(100))


# ------------------ Proveedor ------------------
class Proveedor(db.Model):
    __tablename__ = 'Proveedor'

    ID_Proveedor = db.Column(db.Integer, primary_key=True, autoincrement=True)
    NombreEmpresa = db.Column(db.String(100), nullable=False)
    NombreContacto = db.Column(db.String(100))
    Telefono = db.Column(db.String(20))
    Pais = db.Column(db.String(50))
    CargoContacto = db.Column(db.String(50))

    productos = db.relationship('Producto', back_populates='proveedor',
                                lazy=True)


# ------------------ Categorias ------------------
class Categorias(db.Model):
    __tablename__ = 'Categorias'

    ID_Categoria = db.Column(db.Integer, primary_key=True, autoincrement=True)
    NombreCategoria = db.Column(db.String(100), nullable=False)
    Descripcion = db.Column(db.Text)

    productos = db.relationship('Producto', back_populates='categoria',
                                lazy=True)


# ------------------ Producto ------------------
class Producto(db.Model):
    __tablename__ = 'Producto'

    ID_Producto = db.Column(db.Integer, primary_key=True, autoincrement=True)
    NombreProducto = db.Column(db.String(100), nullable=False)
    Stock = db.Column(db.Integer, nullable=False)
    Material = db.Column(db.String(50))
    PrecioUnidad = db.Column(db.Float, nullable=False)
    Color = db.Column(db.String(30))
    StockMinimo = db.Column(db.Integer, nullable=False, default=0)
    Garantia = db.Column(db.String(255))

    ID_Proveedor = db.Column(db.Integer, db.ForeignKey(
        'Proveedor.ID_Proveedor'), nullable=False)
    ID_Categoria = db.Column(db.Integer, db.ForeignKey(
        'Categorias.ID_Categoria'))

    proveedor = db.relationship('Proveedor', back_populates='productos')
    categoria = db.relationship('Categorias', back_populates='productos')
    imagenes = db.relationship('ImagenProducto', backref='producto', lazy=True)
    novedades = db.relationship('Novedades', backref='producto', lazy=True)
    detalles_pedido = db.relationship('Detalle_Pedido', backref='producto',
                                      lazy=True)
    defectos = db.relationship("Defecto", back_populates="producto")


# ------------------ ImagenProducto ------------------
class ImagenProducto(db.Model):
    __tablename__ = 'ImagenProducto'

    ID_Imagen = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ruta = db.Column(db.String(200), nullable=False)
    ID_Producto = db.Column(db.Integer, db.ForeignKey('Producto.ID_Producto'),
                            nullable=False)


# ------------------ Calendario ------------------
class Calendario(db.Model):
    __tablename__ = 'Calendario'

    ID_Calendario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Fecha = db.Column(db.Date)
    Hora = db.Column(db.Time)
    Ubicacion = db.Column(db.String(200))
    Tipo = db.Column(db.String(50), default="Instalación")

    ID_Usuario = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'),
                           nullable=False)
    ID_Pedido = db.Column(db.Integer, db.ForeignKey('Pedido.ID_Pedido'))

    def to_dict(self):
        """Convierte el evento en un formato compatible con FullCalendar."""
        return {
            "id": self.ID_Calendario,
            "title": f"{self.Tipo} - Pedido {self.ID_Pedido}",
            "start": f"{self.Fecha}T{self.Hora}",
            "color": self.get_color(),
            "extendedProps": {
                "ubicacion": self.Ubicacion,
                "id_usuario": self.ID_Usuario,
                "id_pedido": self.ID_Pedido,
                "tipo": self.Tipo
            }
        }

    def get_color(self):
        colores = {
            "Entrega": "#28a745",
            "Reunión": "#dc3545",
            "Instalación": "#007bff"
        }
        return colores.get(self.Tipo, "#6c757d")


# ------------------ Notificaciones ------------------
class Notificaciones(db.Model):
    __tablename__ = 'Notificaciones'

    ID_Notificacion = db.Column(db.Integer, primary_key=True,
                                autoincrement=True)
    Titulo = db.Column(db.String(200), nullable=False)
    Mensaje = db.Column(db.Text, nullable=False)
    Fecha = db.Column(db.DateTime, default=db.func.current_timestamp())
    Leida = db.Column(db.Boolean, default=False)
    ID_Usuario = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'),
                           nullable=False)


# ------------------ Novedades ------------------
class Novedades(db.Model):
    __tablename__ = 'Novedades'

    ID_Novedad = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Tipo = db.Column(db.String(50))
    EstadoNovedad = db.Column(db.String(50))
    FechaReporte = db.Column(db.Date)

    ID_Usuario = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'),
                           nullable=False)
    ID_Producto = db.Column(db.Integer, db.ForeignKey('Producto.ID_Producto'),
                            nullable=False)


# ------------------ Pedido ------------------
class Pedido(db.Model):
    __tablename__ = 'Pedido'

    ID_Pedido = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Estado = db.Column(db.Enum('pendiente', 'en proceso', 'en reparto',
                               'entregado'))
    FechaPedido = db.Column(db.Date)
    FechaEntrega = db.Column(db.Date)
    Destino = db.Column(db.String(200))
    Descuento = db.Column(db.Float)
    Instalacion = db.Column(db.Integer)

    ID_Usuario = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'),
                           nullable=False)
    ID_Empleado = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'))

    pagos = db.relationship('Pagos', backref='pedido', lazy=True)
    detalles_pedido = db.relationship('Detalle_Pedido', backref='pedido',
                                      lazy=True)
    firmas = db.relationship('Firmas', backref='pedido', lazy=True)
    comentarios = db.relationship('Comentarios', backref='pedido', lazy=True)
    calendario = db.relationship('Calendario', backref='pedido', lazy=True)


# ------------------ Pagos ------------------
class Pagos(db.Model):
    __tablename__ = 'Pagos'

    ID_Pagos = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MetodoPago = db.Column(db.String(50))
    FechaPago = db.Column(db.Date)
    Monto = db.Column(db.Float)
    ID_Pedido = db.Column(db.Integer, db.ForeignKey('Pedido.ID_Pedido'),
                          nullable=False)


# ------------------ Detalle Pedido ------------------
class Detalle_Pedido(db.Model):
    __tablename__ = 'Detalle_Pedido'

    ID_Pedido = db.Column(db.Integer, db.ForeignKey('Pedido.ID_Pedido'),
                          primary_key=True)
    ID_Producto = db.Column(db.Integer, db.ForeignKey('Producto.ID_Producto'),
                            primary_key=True)
    Cantidad = db.Column(db.Integer)
    PrecioUnidad = db.Column(db.Float)


# ------------------ Firmas ------------------
class Firmas(db.Model):
    __tablename__ = 'Firmas'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('Pedido.ID_Pedido'),
                          nullable=False)
    nombre_cliente = db.Column(db.String(100), nullable=False)
    firma = db.Column(db.Text, nullable=False)
    fecha_firma = db.Column(db.DateTime, default=db.func.current_timestamp())


# ------------------ Comentarios ------------------
class Comentarios(db.Model):
    __tablename__ = 'Comentarios'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('Pedido.ID_Pedido',
                                                    ondelete="CASCADE"))
    texto = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=db.func.current_timestamp())


class RegistroEntrega(db.Model):
    __tablename__ = 'RegistroEntrega'

    ID_Registro = db.Column(db.Integer, primary_key=True)
    ID_Pedido = db.Column(db.Integer, db.ForeignKey('Pedido.ID_Pedido'),
                          nullable=False)
    ID_Empleado = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'),
                            nullable=False)
    Comentario = db.Column(db.Text, nullable=True)
    Fotos = db.Column(db.Text, nullable=True)
    FechaRegistro = db.Column(db.DateTime, default=datetime.utcnow)

    pedido = db.relationship('Pedido', backref='registros_entrega')
    empleado = db.relationship('Usuario', backref='registros_realizados')


class Reseñas(db.Model):
    __tablename__ = "Reseñas"

    ID_Reseña = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ID_Usuario = db.Column(db.Integer, db.ForeignKey("Usuario.ID_Usuario"),
                           nullable=False)
    ID_Referencia = db.Column(db.Integer, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    Comentario = db.Column(db.Text, nullable=False)
    Estrellas = db.Column(db.Integer, nullable=False)
    Fecha = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    usuario = db.relationship("Usuario", backref="reseñas", lazy=True)

    def __init__(self, ID_Usuario, ID_Referencia, tipo, Comentario, Estrellas):
        if tipo not in ["producto", "pedido"]:
            raise ValueError(
                "El campo 'tipo' solo puede ser 'producto' o 'pedido'")
        self.ID_Usuario = ID_Usuario
        self.ID_Referencia = ID_Referencia
        self.tipo = tipo
        self.Comentario = Comentario
        self.Estrellas = Estrellas
        self.Fecha = datetime.utcnow()


# ------------------ Registro de Sesiones ------------------
class RegistroSesion(db.Model):
    __tablename__ = 'RegistroSesion'

    ID_Registro = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ID_Usuario = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'),
                           nullable=False)

    Fecha = db.Column(db.Date, nullable=False)
    HoraEntrada = db.Column(db.DateTime, nullable=True)
    HoraSalida = db.Column(db.DateTime, nullable=True)

    usuario = db.relationship('Usuario', backref='registros_sesion')


class PagoEmpleado(db.Model):
    __tablename__ = "Pago_Empleado"

    ID_Pago = db.Column(db.Integer, primary_key=True)
    ID_Empleado = db.Column(db.Integer, db.ForeignKey("Usuario.ID_Usuario"))
    Fecha = db.Column(db.Date)
    Monto = db.Column(db.Float)
    Concepto = db.Column(db.String(100))


class ContratoEmpleado(db.Model):
    __tablename__ = "Contrato_Empleado"

    ID_Contrato = db.Column(db.Integer, primary_key=True)
    ID_Empleado = db.Column(db.Integer, db.ForeignKey("Usuario.ID_Usuario"))
    Archivo = db.Column(db.String(255))
    FechaSubida = db.Column(db.DateTime, default=datetime.utcnow)


class Defecto(db.Model):
    __tablename__ = "defectos"
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey("Producto.ID_Producto"), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=db.func.current_timestamp())
    usuario_id = db.Column(db.Integer, db.ForeignKey("Usuario.ID_Usuario"), nullable=True)

    producto = db.relationship("Producto", back_populates="defectos")
    usuario = db.relationship("Usuario", backref="defectos")


class LoginIntento(db.Model):
    __tablename__ = "LoginIntento"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100))
    ip = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    intentos = db.Column(db.Integer, default=0)
    bloqueado = db.Column(db.Boolean, default=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)


class TokenSeguridad(db.Model):
    __tablename__ = "TokenSeguridad"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100))
    ip = db.Column(db.String(45))
    token = db.Column(db.String(255), unique=True)
    accion = db.Column(db.Enum("si", "no", "desbloquear"))
    usado = db.Column(db.Boolean, default=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
