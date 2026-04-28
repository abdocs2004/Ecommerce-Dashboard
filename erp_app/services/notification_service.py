from flask import current_app
from flask_mail import Message

from ..extensions import db, mail
from ..models import Notification, User


def notify(title, message, type_="info", user_id=None):
    item = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type_,
    )
    db.session.add(item)
    db.session.commit()
    return item


def send_email(subject, recipients, body, html=None):
    if not current_app.config.get("MAIL_USERNAME"):
        return False
    try:
        msg = Message(
            subject=subject,
            recipients=recipients if isinstance(recipients, list) else [recipients],
            body=body,
            html=html,
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Email failed: {e}")
        return False


def notify_order_placed(order):
    notify(
        "Order Placed",
        f"Order #{order.id} has been placed successfully.",
        "success",
        order.user_id,
    )
    if order.user and order.user.email:
        send_email(
            subject=f"Order #{order.id} Confirmation",
            recipients=order.user.email,
            body=f"Thank you for your order! Your order #{order.id} is now pending processing.",
        )


def notify_order_shipped(order):
    notify(
        "Order Shipped",
        f"Order #{order.id} has been shipped.",
        "info",
        order.user_id,
    )
    if order.user and order.user.email:
        send_email(
            subject=f"Order #{order.id} Shipped",
            recipients=order.user.email,
            body=f"Good news! Your order #{order.id} has been shipped and is on its way.",
        )


def notify_low_stock(product):
    notify(
        "Low Stock Alert",
        f"Product '{product.name}' is low on stock ({product.stock} left).",
        "warning",
    )
    staff_emails = [
        u.email for u in db.session.query(User).filter(
            User.role.in_(["super_admin", "admin"])
        ).all()
    ]
    if staff_emails:
        send_email(
            subject="Low Stock Alert",
            recipients=staff_emails,
            body=f"Product '{product.name}' (SKU: {product.sku}) is low on stock. Only {product.stock} units remaining.",
        )


def mark_notification_read(notification_id, user_id):
    notif = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if notif:
        notif.is_read = True
        db.session.commit()
        return True
    return False

