import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, Float, Text, Time, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

# Corregir el "circular import" definiendo la instancia de SQLAlchemy sin la aplicación
# La aplicación se vinculará más tarde en app.py
db = SQLAlchemy()
Base = declarative_base()

class Usuario(db.Model):
    __tablename__ = 'usuario'

    ID_Usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Nombre = db.Column(db.String(80))
    Telefono = db.Column(db.String(60))
    Contraseña = db.Column(db.String(60))
    Direccion = db.Column(db.String(120))
    Correo = db.Column(db.String(120))

    cliente = db.relationship("Cliente", back_populates="usuario", uselist=False)
    administrador = db.relationship("Administrador", back_populates="usuario", uselist=False)
    empleado = db.relationship("Empleado", back_populates="usuario", uselist=False)
    favoritos = db.relationship("Favorito", back_populates="usuario")
    notificaciones = db.relationship("Notificacion", back_populates="usuario")

    def __repr__(self):
        return f"<Usuario(ID={self.ID_Usuario}, Nombre='{self.Nombre}')>"

class Cliente(db.Model):
    __tablename__ = 'cliente'

    ID_Cliente = db.Column(db.Integer, primary_key=True)
    ID_Usuario = db.Column(db.Integer, db.ForeignKey('usuario.ID_Usuario'), unique=True, nullable=False)

    usuario = db.relationship("Usuario", back_populates="cliente")
    pedidos = db.relationship("Pedido", back_populates="cliente")
    devoluciones = db.relationship("Devolucion", back_populates="cliente")
    reseñas = db.relationship("Reseña", back_populates="cliente")

    def __repr__(self):
        return f"<Cliente(ID={self.ID_Cliente}, ID_Usuario={self.ID_Usuario})>"

class Administrador(db.Model):
    __tablename__ = 'administrador'

    ID_Administrador = db.Column(db.Integer, primary_key=True)
    ID_Usuario = db.Column(db.Integer, db.ForeignKey('usuario.ID_Usuario'), unique=True, nullable=False)

    usuario = db.relationship("Usuario", back_populates="administrador")

    def __repr__(self):
        return f"<Administrador(ID={self.ID_Administrador}, ID_Usuario={self.ID_Usuario})>"

class Empleado(db.Model):
    __tablename__ = 'empleado'

    ID_Empleado = db.Column(db.Integer, primary_key=True)
    ID_Usuario = db.Column(db.Integer, db.ForeignKey('usuario.ID_Usuario'), unique=True, nullable=False)
    Cargo = db.Column(db.String(50))

    usuario = db.relationship("Usuario", back_populates="empleado")
    pedidos = db.relationship("Pedido", back_populates="empleado")
    calendarios = db.relationship("Calendario", back_populates="empleado")
    instalaciones = db.relationship("Instalacion", back_populates="empleado")

    def __repr__(self):
        return f"<Empleado(ID={self.ID_Empleado}, Cargo='{self.Cargo}')>"

class Proveedor(db.Model):
    __tablename__ = 'proveedor'

    ID_Proveedor = db.Column(db.Integer, primary_key=True, autoincrement=True)
    NombreEmpresa = db.Column(db.String(100), nullable=False)
    NombreContacto = db.Column(db.String(100))
    CargoContacto = db.Column(db.String(50))
    Pais = db.Column(db.String(50))
    Telefono = db.Column(db.String(20))

    productos = db.relationship("Producto", back_populates="proveedor")

    def __repr__(self):
        return f"<Proveedor(ID={self.ID_Proveedor}, Empresa='{self.NombreEmpresa}')>"

class Pedido(db.Model):
    __tablename__ = 'pedido'

    ID_Pedido = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ID_Cliente = db.Column(db.Integer, db.ForeignKey('cliente.ID_Cliente'), nullable=False)
    ID_Empleado = db.Column(db.Integer, db.ForeignKey('empleado.ID_Empleado'), nullable=True)
    FechaPedido = db.Column(db.Date)
    FechaEntrega = db.Column(db.Date)
    FechaEnvio = db.Column(db.Date)

    cliente = db.relationship("Cliente", back_populates="pedidos")
    empleado = db.relationship("Empleado", back_populates="pedidos")
    detalles_pedido = db.relationship("DetallePedido", back_populates="pedido")
    recibo = db.relationship("Recibo", back_populates="pedido", uselist=False)

    def __repr__(self):
        return f"<Pedido(ID={self.ID_Pedido}, Cliente={self.ID_Cliente}, Fecha='{self.FechaPedido}')>"

class Categoria(db.Model):
    __tablename__ = 'categorias'

    ID_Categoria = db.Column(db.Integer, primary_key=True, autoincrement=True)
    NombreCategoria = db.Column(db.String(100), nullable=False)
    Descripcion = db.Column(db.Text)

    productos = db.relationship("Producto", back_populates="categoria")

    def __repr__(self):
        return f"<Categoria(ID={self.ID_Categoria}, Nombre='{self.NombreCategoria}')>"

class Producto(db.Model):
    __tablename__ = 'producto'

    ID_Producto = db.Column(db.Integer, primary_key=True, autoincrement=True)
    NombreProducto = db.Column(db.String(100), nullable=False)
    Stock = db.Column(db.Integer, nullable=False)
    Material = db.Column(db.String(50))
    PrecioUnidad = db.Column(db.Float, nullable=False)
    Color = db.Column(db.String(30))
    ID_Proveedor = db.Column(db.Integer, db.ForeignKey('proveedor.ID_Proveedor'), nullable=True)
    ID_Categoria = db.Column(db.Integer, db.ForeignKey('categorias.ID_Categoria'), nullable=True)

    proveedor = db.relationship("Proveedor", back_populates="productos")
    categoria = db.relationship("Categoria", back_populates="productos")
    favoritos = db.relationship("Favorito", back_populates="producto")
    devoluciones = db.relationship("Devolucion", back_populates="producto")
    detalles_pedido = db.relationship("DetallePedido", back_populates="producto")
    garantias = db.relationship("Garantia", back_populates="producto")
    reseñas = db.relationship("Reseña", back_populates="producto")

    def __repr__(self):
        return f"<Producto(ID={self.ID_Producto}, Nombre='{self.NombreProducto}')>"

class Favorito(db.Model):
    __tablename__ = 'favoritos'

    ID_Favorito = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ProductosSeleccionados = db.Column(db.Text)
    ID_Usuario = db.Column(db.Integer, db.ForeignKey('usuario.ID_Usuario'), nullable=False)
    ID_Producto = db.Column(db.Integer, db.ForeignKey('producto.ID_Producto'), nullable=False)

    usuario = db.relationship("Usuario", back_populates="favoritos")
    producto = db.relationship("Producto", back_populates="favoritos")

    def __repr__(self):
        return f"<Favorito(ID={self.ID_Favorito}, Usuario={self.ID_Usuario}, Producto={self.ID_Producto})>"

class Devolucion(db.Model):
    __tablename__ = 'devoluciones'

    ID_Devolucion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Motivo = db.Column(db.Text, nullable=False)
    Fecha = db.Column(db.Date, nullable=False)
    ID_Producto = db.Column(db.Integer, db.ForeignKey('producto.ID_Producto'), nullable=False)
    ID_Cliente = db.Column(db.Integer, db.ForeignKey('cliente.ID_Cliente'), nullable=False)

    producto = db.relationship("Producto", back_populates="devoluciones")
    cliente = db.relationship("Cliente", back_populates="devoluciones")

    def __repr__(self):
        return f"<Devolucion(ID={self.ID_Devolucion}, Fecha='{self.Fecha}', Cliente={self.ID_Cliente})>"

class DetallePedido(db.Model):
    __tablename__ = 'detalles_de_pedido'

    ID_DetallesPedido = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ID_Pedido = db.Column(db.Integer, db.ForeignKey('pedido.ID_Pedido'), nullable=False)
    ID_Producto = db.Column(db.Integer, db.ForeignKey('producto.ID_Producto'), nullable=False)
    PrecioUnidad = db.Column(db.Float)
    Cantidad = db.Column(db.Integer)
    Descuento = db.Column(db.Float)

    pedido = db.relationship("Pedido", back_populates="detalles_pedido")
    producto = db.relationship("Producto", back_populates="detalles_pedido")

    def __repr__(self):
        return f"<DetallePedido(ID={self.ID_DetallesPedido}, Pedido={self.ID_Pedido}, Producto={self.ID_Producto})>"

class Garantia(db.Model):
    __tablename__ = 'garantias'

    ID_Garantia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    FechaInicio = db.Column(db.Date, nullable=False)
    FechaFinal = db.Column(db.Date, nullable=False)
    Estado = db.Column(db.String(50))
    ID_Producto = db.Column(db.Integer, db.ForeignKey('producto.ID_Producto'), nullable=False)

    producto = db.relationship("Producto", back_populates="garantias")

    def __repr__(self):
        return f"<Garantia(ID={self.ID_Garantia}, Producto={self.ID_Producto}, Estado='{self.Estado}')>"

class Recibo(db.Model):
    __tablename__ = 'recibo'

    ID_Recibo = db.Column(db.Integer, primary_key=True, autoincrement=True)
    FechaRecibo = db.Column(db.Date, nullable=False)
    MontoTotal = db.Column(db.Float, nullable=False)
    ID_Pedido = db.Column(db.Integer, db.ForeignKey('pedido.ID_Pedido'), nullable=False)

    pedido = db.relationship("Pedido", back_populates="recibo")
    pagos = db.relationship("Pago", back_populates="recibo")

    def __repr__(self):
        return f"<Recibo(ID={self.ID_Recibo}, Pedido={self.ID_Pedido}, Total={self.MontoTotal})>"

class Pago(db.Model):
    __tablename__ = 'pagos'

    ID_Pago = db.Column(db.Integer, primary_key=True, autoincrement=True)
    FechaPago = db.Column(db.Date, nullable=False)
    MetodoPago = db.Column(db.String(50), nullable=False)
    Estado = db.Column(db.String(30))
    Monto = db.Column(db.Float, nullable=False)
    ID_Recibo = db.Column(db.Integer, db.ForeignKey('recibo.ID_Recibo'), nullable=False)

    recibo = db.relationship("Recibo", back_populates="pagos")

    def __repr__(self):
        return f"<Pago(ID={self.ID_Pago}, Metodo='{self.MetodoPago}', Monto={self.Monto})>"

class Calendario(db.Model):
    __tablename__ = 'calendario'

    ID_Calendario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Fecha = db.Column(db.Date, nullable=False)
    Hora = db.Column(db.Time, nullable=False)
    Ubicacion = db.Column(db.String(100))
    ID_Empleado = db.Column(db.Integer, db.ForeignKey('empleado.ID_Empleado'), nullable=False)

    empleado = db.relationship("Empleado", back_populates="calendarios")
    instalaciones = db.relationship("Instalacion", back_populates="calendario")

    def __repr__(self):
        return f"<Calendario(ID={self.ID_Calendario}, Fecha='{self.Fecha}', Hora='{self.Hora}')>"

class Instalacion(db.Model):
    __tablename__ = 'instalacion'

    ID_Instalacion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    FechaInstalacion = db.Column(db.Date, nullable=False)
    Hora = db.Column(db.Time, nullable=False)
    Estado = db.Column(db.String(50))
    ID_Calendario = db.Column(db.Integer, db.ForeignKey('calendario.ID_Calendario'), nullable=False)
    ID_Empleado = db.Column(db.Integer, db.ForeignKey('empleado.ID_Empleado'), nullable=False)

    calendario = db.relationship("Calendario", back_populates="instalaciones")
    empleado = db.relationship("Empleado", back_populates="instalaciones")

    def __repr__(self):
        return f"<Instalacion(ID={self.ID_Instalacion}, Fecha='{self.FechaInstalacion}', Estado='{self.Estado}')>"

class Notificacion(db.Model):
    __tablename__ = 'notificaciones'

    ID_Notificaciones = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Mensaje = db.Column(db.String(255), nullable=False)
    Fecha = db.Column(db.Date)
    ID_Usuario = db.Column(db.Integer, db.ForeignKey('usuario.ID_Usuario'), nullable=False)

    usuario = db.relationship("Usuario", back_populates="notificaciones")

    def __repr__(self):
        return f"<Notificacion(ID={self.ID_Notificaciones}, Mensaje='{self.Mensaje[:20]}...')>"

class Reseña(db.Model):
    __tablename__ = 'reseña'

    ID_Reseña = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Calificacion = db.Column(db.Integer, nullable=False)
    Comentario = db.Column(db.Text)
    Fecha = db.Column(db.Date, nullable=False)
    ID_Cliente = db.Column(db.Integer, db.ForeignKey('cliente.ID_Cliente'), nullable=False)
    ID_Producto = db.Column(db.Integer, db.ForeignKey('producto.ID_Producto'), nullable=True)

    cliente = db.relationship("Cliente", back_populates="reseñas")
    producto = db.relationship("Producto", back_populates="reseñas")

    def __repr__(self):
        return f"<Reseña(ID={self.ID_Reseña}, Calificacion={self.Calificacion}, Cliente={self.ID_Cliente})>"

# Para crear las tablas en tu base de datos (ejemplo con SQLite):
# from sqlalchemy import create_engine
# engine = create_engine('sqlite:///casa_del_arbol.db')
# Base.metadata.create_all(engine)
