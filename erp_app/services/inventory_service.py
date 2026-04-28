from ..extensions import db
from ..models import Product, ProductVariant
from .notification_service import notify_low_stock


def low_stock_items(threshold):
    products = Product.query.filter(Product.stock <= threshold).order_by(Product.stock.asc()).all()
    variants = ProductVariant.query.filter(ProductVariant.stock <= threshold).order_by(ProductVariant.stock.asc()).all()
    return products, variants


def update_stock(product_id, new_stock):
    product = Product.query.get_or_404(product_id)
    old_stock = product.stock
    product.stock = max(int(new_stock), 0)
    db.session.commit()

    # Check if we need to send low stock alert
    threshold = product.low_stock_threshold
    if old_stock > threshold >= product.stock:
        notify_low_stock(product)

    return product


def decrement_stock(product_id, qty):
    product = Product.query.get_or_404(product_id)
    if product.stock < qty:
        raise ValueError(f"Insufficient stock for {product.name}")
    product.stock -= qty
    db.session.commit()

    # Check low stock after decrement
    if product.stock <= product.low_stock_threshold:
        notify_low_stock(product)

    return product

