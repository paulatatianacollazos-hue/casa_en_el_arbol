import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, Float, Text, Time, ForeignKey
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'Usuario'

    ID_Usuario = db.Column(db.Integer, primary_key=True)
    Nombre = db.Column(db.String(100))
    Telefono = db.Column(db.String(20))
    Correo = db.Column(db.String(100))
    Direccion = db.Column(db.String(200))
    Contraseña = db.Column(db.String(100))
    Rol = db.Column(db.String(50))
    Activo = db.Column(db.Boolean)

    calendarios = db.relationship("Calendario", back_populates="usuario")
    notificaciones = db.relationship("Notificaciones", back_populates="usuario")
    pedidos = db.relationship("Pedido", back_populates="usuario")
    novedades = db.relationship("Novedades", back_populates="usuario")


class Proveedor(db.Model):
    __tablename__ = 'Proveedor'

    ID_Proveedor = db.Column(db.Integer, primary_key=True)
    NombreEmpresa = db.Column(db.String(100))
    NombreContacto = db.Column(db.String(100))
    Telefono = db.Column(db.String(20))
    Pais = db.Column(db.String(50))
    CargoContacto = db.Column(db.String(50))

    productos = db.relationship("Producto", back_populates="proveedor")


class Categorias(db.Model):
    __tablename__ = 'Categorias'

    ID_Categoria = db.Column(db.Integer, primary_key=True)
    NombreCategoria = db.Column(db.String(100))
    Descripcion = db.Column(db.Text)

    productos = db.relationship("Producto", back_populates="categoria")


class Calendario(db.Model):
    __tablename__ = 'Calendario'

    ID_Calendario = db.Column(db.Integer, primary_key=True)
    Fecha = db.Column(db.Date)
    Hora = db.Column(db.Time)
    Ubicacion = db.Column(db.String(200))
    ID_Usuario = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'))

    usuario = db.relationship("Usuario", back_populates="calendarios")


class Notificaciones(db.Model):
    __tablename__ = 'Notificaciones'

    ID_Notificacion = db.Column(db.Integer, primary_key=True)
    Fecha = db.Column(db.Date)
    Mensaje = db.Column(db.Text)
    ID_Usuario = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'))

    usuario = db.relationship("Usuario", back_populates="notificaciones")


class Producto(db.Model):
    __tablename__ = 'Producto'

    ID_Producto = db.Column(db.Integer, primary_key=True)
    NombreProducto = db.Column(db.String(100))
    Stock = db.Column(db.Integer)
    Material = db.Column(db.String(50))
    Color = db.Column(db.String(30))
    PrecioUnidad = db.Column(db.Float)
    ID_Categoria = db.Column(db.Integer, db.ForeignKey('Categorias.ID_Categoria'))
    ID_Proveedor = db.Column(db.Integer, db.ForeignKey('Proveedor.ID_Proveedor'))

    categoria = db.relationship("Categorias", back_populates="productos")
    proveedor = db.relationship("Proveedor", back_populates="productos")
    novedades = db.relationship("Novedades", back_populates="producto")
    detalles_pedido = db.relationship("DetallePedido", back_populates="producto")


class Novedades(db.Model):
    __tablename__ = 'Novedades'

    ID_Novedad = db.Column(db.Integer, primary_key=True)
    Tipo = db.Column(db.String(50))  # Garantía, devolución
    EstadoNovedad = db.Column(db.String(50))
    FechaReporte = db.Column(db.Date)
    ID_Usuario = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'))
    ID_Producto = db.Column(db.Integer, db.ForeignKey('Producto.ID_Producto'))

    usuario = db.relationship("Usuario", back_populates="novedades")
    producto = db.relationship("Producto", back_populates="novedades")


class Pedido(db.Model):
    __tablename__ = 'Pedido'

    ID_Pedido = db.Column(db.Integer, primary_key=True)
    NombreComprador = db.Column(db.String(100))
    Estado = db.Column(db.String(50))
    FechaPedido = db.Column(db.Date)
    FechaEntrega = db.Column(db.Date)
    Destino = db.Column(db.String(200))
    Descuento = db.Column(db.Float)
    ID_Usuario = db.Column(db.Integer, db.ForeignKey('Usuario.ID_Usuario'))

    usuario = db.relationship("Usuario", back_populates="pedidos")
    pagos = db.relationship("Pagos", back_populates="pedido")
    detalles_pedido = db.relationship("DetallePedido", back_populates="pedido")


class Pagos(db.Model):
    __tablename__ = 'Pagos'

    ID_Pagos = db.Column(db.Integer, primary_key=True)
    MetodoPago = db.Column(db.String(50))
    FechaPago = db.Column(db.Date)
    Monto = db.Column(db.Float)
    ID_Pedido = db.Column(db.Integer, db.ForeignKey('Pedido.ID_Pedido'))

    pedido = db.relationship("Pedido", back_populates="pagos")


class DetallePedido(db.Model):
    __tablename__ = 'Detalle_Pedido'

    ID_Pedido = db.Column(db.Integer, db.ForeignKey('Pedido.ID_Pedido'), primary_key=True)
    ID_Producto = db.Column(db.Integer, db.ForeignKey('Producto.ID_Producto'), primary_key=True)
    Cantidad = db.Column(db.Integer)
    PrecioUnidad = db.Column(db.Float)

    pedido = db.relationship("Pedido", back_populates="detalles_pedido")
    producto = db.relationship("Producto", back_populates="detalles_pedido")
