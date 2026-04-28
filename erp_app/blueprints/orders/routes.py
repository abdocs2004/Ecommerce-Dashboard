from flask import Blueprint, abort, flash, redirect, render_template, request, send_from_directory, session, url_for
from flask_login import current_user, login_required

from ...models import Order, Product, User
from ...security import staff_required
from ...services.order_service import ORDER_STATUSES, assign_order, create_order_from_cart, update_order_status

orders_bp = Blueprint("orders", __name__)


@orders_bp.route("/cart/add/<int:product_id>")
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)

    if product.stock < 1:
        flash(f"{product.name} is out of stock", "warning")
        return redirect(url_for("products.catalog"))

    cart = session.get("cart", [])
    for item in cart:
        if item["product_id"] == product.id:
            if item["quantity"] >= product.stock:
                flash(f"Maximum available quantity for {product.name} is {product.stock}", "warning")
                return redirect(url_for("products.catalog"))
            item["quantity"] += 1
            break
    else:
        cart.append({"product_id": product.id, "quantity": 1})
    session["cart"] = cart
    flash(f"Added {product.name} to cart", "success")
    return redirect(url_for("products.catalog"))


@orders_bp.route("/cart")
@login_required
def cart():
    cart = session.get("cart", [])
    products_map = {p.id: p for p in Product.query.filter(Product.id.in_([i["product_id"] for i in cart] or [0])).all()}
    rows = []
    total = 0.0
    for item in cart:
        product = products_map.get(item["product_id"])
        if not product:
            continue
        subtotal = float(product.price) * item["quantity"]
        total += subtotal
        rows.append({"product": product, "quantity": item["quantity"], "subtotal": subtotal})
    return render_template("orders/cart.html", rows=rows, total=total)


@orders_bp.route("/cart/update/<int:product_id>", methods=["POST"])
@login_required
def update_cart_item(product_id):
    qty = request.form.get("quantity", type=int, default=1)
    product = Product.query.get_or_404(product_id)

    if qty > product.stock:
        flash(f"Only {product.stock} available for {product.name}", "warning")
        return redirect(url_for("orders.cart"))

    cart = session.get("cart", [])
    for item in cart:
        if item["product_id"] == product_id:
            if qty <= 0:
                cart.remove(item)
            else:
                item["quantity"] = qty
            break
    session["cart"] = cart
    return redirect(url_for("orders.cart"))


@orders_bp.route("/cart/remove/<int:product_id>")
@login_required
def remove_from_cart(product_id):
    cart = session.get("cart", [])
    cart = [item for item in cart if item["product_id"] != product_id]
    session["cart"] = cart
    flash("Item removed from cart", "info")
    return redirect(url_for("orders.cart"))


@orders_bp.route("/checkout", methods=["POST"])
@login_required
def checkout():
    cart = session.get("cart", [])
    if not cart:
        flash("Your cart is empty", "warning")
        return redirect(url_for("orders.cart"))

    # Validate stock before creating order
    for cart_item in cart:
        product = Product.query.get(cart_item["product_id"])
        if not product or product.stock < cart_item["quantity"]:
            flash(f"Insufficient stock for {product.name if product else 'product'}", "danger")
            return redirect(url_for("orders.cart"))

    try:
        order, invoice = create_order_from_cart(current_user, cart)
        session["cart"] = []
        flash(f"Order #{order.id} placed successfully", "success")
        return redirect(url_for("orders.my_orders"))
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("orders.cart"))


@orders_bp.route("/my")
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template("orders/my_orders.html", orders=orders)


@orders_bp.route("/manage")
@login_required
@staff_required
def manage_orders():
    status = request.args.get("status", "")
    query = Order.query
    if status:
        query = query.filter_by(status=status)
    orders = query.order_by(Order.created_at.desc()).all()
    staff_users = User.query.filter(User.role.in_(["admin", "staff"])).all()
    return render_template("orders/manage.html", orders=orders, statuses=ORDER_STATUSES, current_status=status, staff_users=staff_users)


@orders_bp.route("/<int:order_id>/status", methods=["POST"])
@login_required
@staff_required
def change_status(order_id):
    status = request.form.get("status", "")
    update_order_status(order_id, status)
    flash("Order status updated", "success")
    return redirect(url_for("orders.manage_orders"))


@orders_bp.route("/<int:order_id>/assign", methods=["POST"])
@login_required
@staff_required
def assign_order_route(order_id):
    staff_id = request.form.get("staff_id", type=int)
    if staff_id:
        assign_order(order_id, staff_id)
        flash("Order assigned successfully", "success")
    return redirect(url_for("orders.manage_orders"))


@orders_bp.route("/<int:order_id>/invoice")
@login_required
def view_invoice(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and current_user.role not in {"super_admin", "admin", "staff"}:
        abort(403)

    if not order.invoice:
        flash("Invoice not found", "warning")
        return redirect(url_for("orders.my_orders"))

    return send_from_directory(
        "static",
        order.invoice.pdf_path,
        as_attachment=False,
    )

