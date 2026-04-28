from sqlalchemy import func

from ..extensions import db
from ..models import CustomerProfile, Order, User


def list_customers(search=""):
    query = User.query.filter(User.role == "customer")
    if search:
        query = query.filter(User.name.ilike(f"%{search}%"))
    return query.order_by(User.created_at.desc()).all()


def top_customers(limit=5):
    results = (
        User.query.join(Order, User.id == Order.user_id)
        .with_entities(User, func.count(Order.id).label("orders_count"))
        .group_by(User.id)
        .order_by(func.count(Order.id).desc())
        .limit(limit)
        .all()
    )
    return results


def update_customer_tags(user_id, tags):
    profile = CustomerProfile.query.get(user_id)
    if not profile:
        profile = CustomerProfile(user_id=user_id)
    profile.tags = tags
    db.session.add(profile)
    db.session.commit()
    return profile


def create_customer(name, email, password, phone="", address="", tags="new"):
    if User.query.filter_by(email=email).first():
        raise ValueError("Email already exists")

    user = User(name=name, email=email, role="customer")
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    profile = CustomerProfile(
        user_id=user.id,
        phone=phone,
        address=address,
        tags=tags,
    )
    db.session.add(profile)
    db.session.commit()
    return user


def get_customer_orders(user_id):
    return Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()

