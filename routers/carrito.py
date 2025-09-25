from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from basedatos.models import db, Producto  
from flask_login import login_required

carrito = Blueprint('carrito', __name__, url_prefix='/carrito')

@carrito.route("/add", methods=["POST"])
def add_to_cart():
    data = request.get_json()

    try:
        product_id = int(data.get("id"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "ID inválido"}), 400

    if "cart" not in session:
        session["cart"] = []

    if product_id not in session["cart"]:
        session["cart"].append(product_id)

    session.modified = True

    return jsonify({
        "success": True,
        "cart_count": len(session["cart"])
    })


@carrito.route("/", methods=["GET"])
def ver_carrito():
    ids = session.get("cart", [])

    try:
        ids = [int(i) for i in ids]
    except:
        ids = []

    productos = Producto.query.filter(Producto.ID_Producto.in_(ids)).all() if ids else []

    print("🛒 Productos encontrados:", [p.NombreProducto for p in productos])

    return render_template("carrito.html", productos=productos)


@carrito.route("/remove/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id):
    cart = session.get("cart", [])

    try:
        cart = [int(i) for i in cart]
    except:
        pass

    if product_id in cart:
        cart.remove(product_id)
        session["cart"] = cart
        session.modified = True
        flash("Producto eliminado del carrito", "success")

    return redirect(url_for("carrito.ver_carrito"))
