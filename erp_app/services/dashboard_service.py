from flask import current_app

from .inventory_service import low_stock_items
from .report_service import best_sellers, sales_chart_data, sales_summary


def dashboard_data():
    threshold = current_app.config["LOW_STOCK_THRESHOLD"]
    products, variants = low_stock_items(threshold)
    return {
        "summary": sales_summary(),
        "sales_chart": sales_chart_data(),
        "best_sellers": best_sellers(),
        "low_stock_products": products,
        "low_stock_variants": variants,
    }

