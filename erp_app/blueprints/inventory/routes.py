from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from ...security import staff_required
from ...services.inventory_service import low_stock_items, update_stock

inventory_bp = Blueprint("inventory", __name__)


@inventory_bp.route("/")
@login_required
@staff_required
def overview():
    threshold = request.args.get("threshold", type=int, default=999999)
    products, variants = low_stock_items(threshold=threshold)
    return render_template("inventory/overview.html", products=products, variants=variants, threshold=threshold)


@inventory_bp.route("/<int:product_id>/stock", methods=["POST"])
@login_required
@staff_required
def stock(product_id):
    update_stock(product_id, request.form.get("stock", type=int))
    flash("Stock updated", "success")
    return redirect(url_for("inventory.overview"))

