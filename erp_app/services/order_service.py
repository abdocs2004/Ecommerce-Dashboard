from decimal import Decimal

from ..extensions import db
from ..models import Order, OrderItem, Product
from .invoice_service import create_invoice
from .inventory_service import decrement_stock
from .notification_service import notify, notify_order_placed


ORDER_STATUSES = ["pending", "processing", "shipped", "delivered", "cancelled"]


def create_order_from_cart(user, cart_items):
    order = Order(user_id=user.id, status="pending")
    db.session.add(order)
    db.session.flush()

    total = Decimal("0.00")
    for cart_item in cart_items:
        product = Product.query.get_or_404(cart_item["product_id"])
        qty = int(cart_item["quantity"])

        # Check stock availability
        if product.stock < qty:
            db.session.rollback()
            raise ValueError(f"Insufficient stock for {product.name}. Only {product.stock} available.")

        decrement_stock(product.id, qty)
        line_price = Decimal(str(product.price))
        total += line_price * qty

        db.session.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=qty,
                price=line_price,
                product_name=product.name,
            )
        )

    order.total_price = total
    db.session.commit()

    invoice = create_invoice(order)
    notify_order_placed(order)
    return order, invoice


def update_order_status(order_id, new_status):
    if new_status not in ORDER_STATUSES:
        raise ValueError("Invalid status")
    order = Order.query.get_or_404(order_id)
    old_status = order.status
    order.status = new_status
    db.session.commit()

    notify(
        "Order Status Updated",
        f"Order #{order.id} status changed from {old_status} to {new_status}",
        "info",
        order.user_id,
    )

    if new_status == "shipped":
        from .notification_service import notify_order_shipped
        notify_order_shipped(order)

    return order


def assign_order(order_id, staff_id):
    order = Order.query.get_or_404(order_id)
    order.assigned_staff_id = staff_id
    db.session.commit()
    notify(
        "Order Assigned",
        f"Order #{order.id} assigned to staff.",
        "info",
        staff_id,
    )
    return order

