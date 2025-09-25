from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

reviews = []

reseña = Blueprint('reseña', __name__, url_prefix='/reseña')

@reseña.route('/reseñas')
def reseñas():
    if reviews:
        avg = round(sum([int(r['estrellas']) for r in reviews]) / len(reviews), 2)
    else:
        avg = "N/A"
    return render_template("reseñas.html", reviews=reviews, avg=avg)

@reseña.route('/escribir', methods=['GET', 'POST'])
@login_required
def escribir():
    if request.method == 'POST':
        pedido = request.form['pedido']
        cliente = request.form['cliente']
        estrellas = request.form['estrellas']
        comentario = request.form['comentario']
        reviews.append({"pedido": pedido, "cliente": cliente, "estrellas": estrellas, "comentario": comentario})
        flash("Reseña añadida con éxito", "success")
        return redirect(url_for('reseña.reseñas'))
    return render_template("escribir.html")

@reseña.route('/admin')
@login_required
def admin():
    # Aquí podrías agregar algún filtro o control de acceso según roles
    return render_template("administrador/admin_reseñas.html", reviews=reviews)
