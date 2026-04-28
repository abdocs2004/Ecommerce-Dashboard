from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ...extensions import db
from ...models import Product, ProductVariant
from ...security import admin_required
from ...services.product_service import all_categories, create_product, list_products, save_image, update_product

products_bp = Blueprint("products", __name__)


@products_bp.route("/")
@login_required
def catalog():
    search = request.args.get("q", "")
    category_id = request.args.get("category_id", type=int)
    products = list_products(
        name=search,
        category_id=category_id,
        is_active=True,
    )
    categories = all_categories()
    return render_template("products/catalog.html", products=products, categories=categories, search=search, selected_category=category_id)


@products_bp.route("/manage")
@login_required
@admin_required
def manage():
    products = list_products(
        name=request.args.get("name", ""),
        category_id=request.args.get("category_id", type=int),
    )
    categories = all_categories()
    return render_template("products/manage.html", products=products, categories=categories)


@products_bp.route("/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_product():
    categories = all_categories()
    if request.method == "POST":
        image_file = request.files.get("image")
        image_url = save_image(image_file) if image_file else ""

        product = create_product(
            name=request.form["name"],
            sku=request.form["sku"],
            description=request.form.get("description", ""),
            price=request.form.get("price", type=float),
            stock=request.form.get("stock", type=int),
            cost=request.form.get("cost", type=float, default=0),
            category_id=request.form.get("category_id", type=int),
            tags_csv=request.form.get("tags", ""),
        )

        if image_url:
            product.image_url = image_url
            db.session.commit()

        sizes = request.form.getlist("variant_size")
        colors = request.form.getlist("variant_color")
        stocks = request.form.getlist("variant_stock")
        for i in range(len(sizes)):
            if not sizes[i] or not colors[i]:
                continue
            db.session.add(
                ProductVariant(
                    product_id=product.id,
                    size=sizes[i],
                    color=colors[i],
                    stock=int(stocks[i] or 0),
                )
            )
        db.session.commit()

        flash("Product added successfully", "success")
        return redirect(url_for("products.manage"))

    return render_template("products/new.html", categories=categories)


@products_bp.route("/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    categories = all_categories()

    if request.method == "POST":
        image_file = request.files.get("image")
        image_url = save_image(image_file) if image_file else None

        update_product(
            product_id=product.id,
            name=request.form.get("name", product.name),
            sku=request.form.get("sku", product.sku),
            description=request.form.get("description", product.description),
            price=request.form.get("price", type=float, default=product.price),
            stock=request.form.get("stock", type=int, default=product.stock),
            cost=request.form.get("cost", type=float, default=product.cost),
            category_id=request.form.get("category_id", type=int, default=product.category_id),
            is_active=bool(request.form.get("is_active")),
            tags_csv=request.form.get("tags", ""),
        )

        if image_url:
            product.image_url = image_url
            db.session.commit()

        flash("Product updated successfully", "success")
        return redirect(url_for("products.manage"))

    return render_template("products/edit.html", product=product, categories=categories)


@products_bp.route("/<int:product_id>/toggle")
@login_required
@admin_required
def toggle_active(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_active = not product.is_active
    db.session.commit()
    flash("Product status updated", "info")
    return redirect(url_for("products.manage"))

