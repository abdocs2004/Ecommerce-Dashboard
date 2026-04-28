import os
from datetime import datetime

from flask import current_app
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from ..extensions import db
from ..models import Invoice


def create_invoice(order):
    existing = Invoice.query.filter_by(order_id=order.id).first()
    if existing:
        return existing

    invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{order.id:05d}"
    invoice = Invoice(order_id=order.id, invoice_number=invoice_number)
    db.session.add(invoice)
    db.session.flush()

    folder = os.path.join(current_app.root_path, "static", "invoices")
    os.makedirs(folder, exist_ok=True)
    pdf_filename = f"{invoice_number}.pdf"
    pdf_path = os.path.join(folder, pdf_filename)

    _generate_pdf(order, invoice_number, pdf_path)
    invoice.pdf_path = f"invoices/{pdf_filename}"
    db.session.commit()
    return invoice


def _generate_pdf(order, invoice_number, path):
    c = canvas.Canvas(path, pagesize=A4)
    y = 800
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"Invoice {invoice_number}")
    y -= 30
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Order ID: {order.id}")
    y -= 20
    c.drawString(50, y, f"Customer: {order.user.name} ({order.user.email})")
    y -= 20
    c.drawString(50, y, f"Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}")
    y -= 30

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Product")
    c.drawString(280, y, "Qty")
    c.drawString(340, y, "Price")
    c.drawString(430, y, "Line Total")
    y -= 20

    c.setFont("Helvetica", 11)
    for item in order.items:
        c.drawString(50, y, item.product_name[:35])
        c.drawString(280, y, str(item.quantity))
        c.drawString(340, y, f"{float(item.price):.2f}")
        c.drawString(430, y, f"{float(item.price) * item.quantity:.2f}")
        y -= 18

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"Total: {float(order.total_price):.2f}")
    c.save()

