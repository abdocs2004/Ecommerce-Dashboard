import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ...extensions import db
from ...models import Notification, Order, User
from ...security import admin_required, staff_required
from ...services.crm_service import create_customer
from ...services.dashboard_service import dashboard_data

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/dashboard")
@login_required
@staff_required
def dashboard():
    data = dashboard_data()
    notifications = Notification.query.order_by(Notification.created_at.desc()).limit(8).all()
    sales_chart = json.dumps(data["sales_chart"])
    return render_template("admin/dashboard.html", data=data, notifications=notifications, sales_chart=sales_chart)


@admin_bp.route("/reports")
@login_required
@admin_required
def reports():
    data = dashboard_data()
    return render_template("admin/reports.html", data=data)


@admin_bp.route("/customers/create", methods=["POST"])
@login_required
@admin_required
def create_customer_admin():
    try:
        create_customer(
            name=request.form.get("name", "").strip(),
            email=request.form.get("email", "").strip().lower(),
            password=request.form.get("password", ""),
            phone=request.form.get("phone", "").strip(),
            address=request.form.get("address", "").strip(),
            tags=request.form.get("tags", "new"),
        )
        flash("Customer created successfully", "success")
    except ValueError as e:
        flash(str(e), "warning")
    return redirect(url_for("crm.customers"))


@admin_bp.route("/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_notification_read(notification_id):
    notif = Notification.query.get_or_404(notification_id)
    is_admin = current_user.role in {"super_admin", "admin"}
    if notif.user_id and notif.user_id != current_user.id and not is_admin:
        flash("Unauthorized", "danger")
        return redirect(url_for("admin.dashboard"))
    notif.is_read = True
    db.session.commit()
    return redirect(request.referrer or url_for("admin.dashboard"))

