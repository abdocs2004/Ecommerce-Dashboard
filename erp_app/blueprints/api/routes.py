from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from ...extensions import db
from ...models import Category, Order, Product, User
from ...security import admin_required, staff_required

api_bp = Blueprint("api", __name__)


def _user_to_dict(u):
    return {
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "role": u.role,
        "gender": u.gender,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


def _product_to_dict(p):
    return {
        "id": p.id,
        "name": p.name,
        "sku": p.sku,
        "description": p.description,
        "price": float(p.price),
        "cost": float(p.cost) if p.cost else 0,
        "stock": p.stock,
        "category": p.category.name if p.category else None,
        "category_id": p.category_id,
        "image_url": p.image_url,
        "is_active": p.is_active,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


def _order_to_dict(o):
    return {
        "id": o.id,
        "user": _user_to_dict(o.user) if o.user else None,
        "total_price": float(o.total_price),
        "status": o.status,
        "assigned_staff_id": o.assigned_staff_id,
        "created_at": o.created_at.isoformat() if o.created_at else None,
        "items": [
            {
                "product_id": i.product_id,
                "product_name": i.product_name,
                "quantity": i.quantity,
                "price": float(i.price),
            }
            for i in o.items
        ],
    }


# ============== PRODUCTS API (Full CRUD) ==============
@api_bp.route("/api/products", methods=["GET"])
def api_products():
    """Get all active products (public)"""
    products = Product.query.filter(Product.is_active == True).all()
    return jsonify([_product_to_dict(p) for p in products])


@api_bp.route("/api/products/<int:product_id>", methods=["GET"])
def api_product_detail(product_id):
    """Get single product by ID (public)"""
    product = Product.query.get_or_404(product_id)
    return jsonify(_product_to_dict(product))


@api_bp.route("/api/products", methods=["POST"])
@login_required
@admin_required
def api_create_product():
    """Create new product (admin only)"""
    data = request.get_json() or request.form

    name = data.get("name", "").strip()
    sku = data.get("sku", "").strip()
    description = data.get("description", "").strip()
    price = float(data.get("price", 0))
    stock = int(data.get("stock", 0))
    category_id = int(data.get("category_id", 0))
    cost = float(data.get("cost", 0))

    if not name or not sku or price <= 0:
        return jsonify({"error": "Name, SKU and positive price are required"}), 400

    if Product.query.filter_by(sku=sku).first():
        return jsonify({"error": f"SKU '{sku}' already exists"}), 400

    if not Category.query.get(category_id):
        return jsonify({"error": "Invalid category_id"}), 400

    product = Product(
        name=name,
        sku=sku,
        description=description,
        price=price,
        cost=cost,
        stock=stock,
        category_id=category_id,
        is_active=True,
    )
    db.session.add(product)
    db.session.commit()

    return jsonify({"message": "Product created", "product": _product_to_dict(product)}), 201


@api_bp.route("/api/products/<int:product_id>", methods=["PUT"])
@login_required
@admin_required
def api_update_product(product_id):
    """Update product (admin only)"""
    product = Product.query.get_or_404(product_id)
    data = request.get_json() or request.form

    product.name = data.get("name", product.name).strip()
    product.description = data.get("description", product.description)
    product.price = float(data.get("price", product.price))
    product.cost = float(data.get("cost", product.cost))
    product.stock = int(data.get("stock", product.stock))
    product.is_active = data.get("is_active", product.is_active)

    if "category_id" in data:
        cid = int(data["category_id"])
        if Category.query.get(cid):
            product.category_id = cid

    db.session.commit()
    return jsonify({"message": "Product updated", "product": _product_to_dict(product)})


@api_bp.route("/api/products/<int:product_id>", methods=["DELETE"])
@login_required
@admin_required
def api_delete_product(product_id):
    """Delete product (admin only) - soft delete by deactivating"""
    product = Product.query.get_or_404(product_id)
    product.is_active = False
    db.session.commit()
    return jsonify({"message": f"Product #{product_id} deactivated"})


# ============== PROTECTED API (Staff only) ==============
@api_bp.route("/api/users")
@login_required
@staff_required
def api_users():
    users = User.query.all()
    return jsonify([_user_to_dict(u) for u in users])


@api_bp.route("/api/orders")
@login_required
@staff_required
def api_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return jsonify([_order_to_dict(o) for o in orders])


@api_bp.route("/api/orders/<int:order_id>")
@login_required
@staff_required
def api_order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify(_order_to_dict(order))


# ============== CUSTOMER OWN DATA ==============
@api_bp.route("/api/my-orders")
@login_required
def api_my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return jsonify([_order_to_dict(o) for o in orders])

