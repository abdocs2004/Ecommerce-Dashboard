import os
import secrets

from flask import current_app
from PIL import Image
from sqlalchemy import func

from ..extensions import db
from ..models import Category, Product, Tag


def list_products(name=None, category_id=None, is_active=None):
    query = Product.query
    if name:
        query = query.filter(Product.name.ilike(f"%{name}%"))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    return query.order_by(Product.created_at.desc()).all()


def create_product(name, sku, description, price, stock, category_id, cost=0, tags_csv=""):
    product = Product(
        name=name,
        sku=sku,
        description=description,
        price=price,
        stock=stock,
        cost=cost,
        category_id=category_id,
    )
    product.tags = _resolve_tags(tags_csv)
    db.session.add(product)
    db.session.commit()
    return product


def update_product(product_id, **kwargs):
    product = Product.query.get_or_404(product_id)
    for key, value in kwargs.items():
        if hasattr(product, key) and value is not None:
            setattr(product, key, value)
    if "tags_csv" in kwargs:
        product.tags = _resolve_tags(kwargs["tags_csv"])
    db.session.commit()
    return product


def _resolve_tags(tags_csv):
    tags = []
    for raw in [x.strip() for x in tags_csv.split(",") if x.strip()]:
        tag = Tag.query.filter(func.lower(Tag.name) == raw.lower()).first()
        if not tag:
            tag = Tag(name=raw)
            db.session.add(tag)
        tags.append(tag)
    return tags


def all_categories():
    return Category.query.order_by(Category.name.asc()).all()


def save_image(image_file, folder="products"):
    if not image_file:
        return None

    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(image_file.filename)
    picture_fn = random_hex + f_ext

    upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], folder)
    os.makedirs(upload_path, exist_ok=True)

    picture_path = os.path.join(upload_path, picture_fn)

    # Resize image
    output_size = (800, 800)
    i = Image.open(image_file)
    i.thumbnail(output_size)
    i.save(picture_path)

    return f"{folder}/{picture_fn}"

