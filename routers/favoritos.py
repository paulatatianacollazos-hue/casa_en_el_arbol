from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from basedatos.models import db, Producto  

favoritos = Blueprint('favoritos', __name__, url_prefix='/favoritos')

@favoritos.route("/add_to_favorites", methods=["POST"])
def add_to_favorites():
    data = request.get_json() or {}
    try:
        product_id = int(data.get("id"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "ID inválido"}), 400

    if "favorites" not in session:
        session["favorites"] = []

    favs = list(map(int, session.get("favorites", [])))
    if product_id not in favs:
        favs.append(product_id)

    session["favorites"] = favs
    session.modified = True

    return jsonify({"success": True, "fav_count": len(session["favorites"])})

@favoritos.route("/")
def ver_favoritos():  # ✅ Renombrado
    ids = session.get("favorites", [])
    try:
        ids_int = [int(i) for i in ids]
    except Exception:
        ids_int = []

    productos = Producto.query.filter(Producto.ID_Producto.in_(ids_int)).all() if ids_int else []
    return render_template("favoritos.html", productos=productos)

@favoritos.route("/remove_from_favorites/<int:product_id>", methods=["POST"])
def remove_from_favorites(product_id):
    favs = session.get("favorites", [])
    try:
        favs = [int(i) for i in favs]
    except:
        pass

    if product_id in favs:
        favs.remove(product_id)
        session["favorites"] = favs
        session.modified = True
        flash("Producto eliminado de favoritos", "success")

    return redirect(url_for("favoritos.ver_favoritos"))
