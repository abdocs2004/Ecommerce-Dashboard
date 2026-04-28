from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from ...security import admin_required
from ...services.crm_service import get_customer_orders, list_customers, top_customers, update_customer_tags

crm_bp = Blueprint("crm", __name__)


@crm_bp.route("/")
@login_required
@admin_required
def customers():
    customers_list = list_customers(request.args.get("q", ""))
    leaders = top_customers()
    return render_template("crm/customers.html", customers=customers_list, leaders=leaders)


@crm_bp.route("/<int:user_id>")
@login_required
@admin_required
def customer_detail(user_id):
    from ...models import User
    customer = User.query.get_or_404(user_id)
    if customer.role != "customer":
        flash("Not a customer account", "warning")
        return redirect(url_for("crm.customers"))
    orders = get_customer_orders(user_id)
    return render_template("crm/customer_detail.html", customer=customer, orders=orders)


@crm_bp.route("/<int:user_id>/tags", methods=["POST"])
@login_required
@admin_required
def tags(user_id):
    update_customer_tags(user_id, request.form.get("tags", "new"))
    flash("Customer tags updated", "success")
    return redirect(url_for("crm.customers"))

