from datetime import datetime

from sqlalchemy import func

from ..models import Order, OrderItem, Product, User


def sales_summary():
    revenue = func.coalesce(func.sum(Order.total_price), 0)
    total_revenue = Order.query.with_entities(revenue).scalar()
    total_orders = Order.query.count()
    total_customers = User.query.filter_by(role="customer").count()
    total_products = Product.query.count()
    return {
        "revenue": float(total_revenue or 0),
        "orders": total_orders,
        "customers": total_customers,
        "products": total_products,
    }


def best_sellers(limit=5):
    rows = (
        OrderItem.query.with_entities(
            OrderItem.product_name,
            func.sum(OrderItem.quantity).label("sold_qty"),
        )
        .group_by(OrderItem.product_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
        .all()
    )
    return rows


def sales_chart_data():
    rows = (
        Order.query.with_entities(
            func.date(Order.created_at).label("day"),
            func.sum(Order.total_price).label("sales"),
        )
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
        .all()
    )
    return [{"day": str(day), "sales": float(sales or 0)} for day, sales in rows]


def inventory_report():
    return Product.query.order_by(Product.stock.asc()).all()


def sales_report(from_date=None, to_date=None):
    query = Order.query
    if from_date:
        query = query.filter(func.date(Order.created_at) >= from_date)
    if to_date:
        query = query.filter(func.date(Order.created_at) <= to_date)
    orders = query.order_by(Order.created_at.desc()).all()
    total = sum(float(o.total_price) for o in orders)
    return {"orders": orders, "total": total, "count": len(orders)}


def customer_report():
    customers = (
        User.query.filter_by(role="customer")
        .outerjoin(Order, User.id == Order.user_id)
        .with_entities(
            User,
            func.count(Order.id).label("order_count"),
            func.coalesce(func.sum(Order.total_price), 0).label("total_spent"),
        )
        .group_by(User.id)
        .order_by(func.sum(Order.total_price).desc())
        .all()
    )
    return customers


def profit_report():
    products = Product.query.all()
    report = []
    total_profit = 0
    total_revenue = 0
    total_cost = 0

    for p in products:
        sold_qty = (
            OrderItem.query.with_entities(func.sum(OrderItem.quantity))
            .filter_by(product_id=p.id)
            .scalar() or 0
        )
        revenue = float(p.price) * sold_qty
        cost = float(p.cost) * sold_qty
        profit = revenue - cost
        total_profit += profit
        total_revenue += revenue
        total_cost += cost

        report.append({
            "product": p,
            "sold_qty": sold_qty,
            "revenue": revenue,
            "cost": cost,
            "profit": profit,
        })

    return {
        "products": report,
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "total_profit": total_profit,
    }

