from flask import Blueprint, render_template, request
from flask_login import login_required

from ...security import admin_required
from ...services.report_service import customer_report, inventory_report, profit_report, sales_report

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/sales")
@login_required
@admin_required
def sales():
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")
    data = sales_report(from_date=from_date, to_date=to_date)
    return render_template("reports/sales.html", data=data, from_date=from_date, to_date=to_date)


@reports_bp.route("/customers")
@login_required
@admin_required
def customers():
    data = customer_report()
    return render_template("reports/customers.html", customers=data)


@reports_bp.route("/inventory")
@login_required
@admin_required
def inventory():
    products = inventory_report()
    return render_template("reports/inventory.html", products=products)


@reports_bp.route("/profit")
@login_required
@admin_required
def profit():
    data = profit_report()
    return render_template("reports/profit.html", data=data)

