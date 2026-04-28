from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, login_manager


product_tags = db.Table(
    "product_tags",
    db.Column("product_id", db.Integer, db.ForeignKey("products.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"), primary_key=True),
)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="customer")
    gender = db.Column(db.String(10), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    profile = db.relationship("CustomerProfile", back_populates="user", uselist=False)
    orders = db.relationship("Order", back_populates="user", foreign_keys="Order.user_id")
    assigned_orders = db.relationship(
        "Order",
        foreign_keys="Order.assigned_staff_id",
        back_populates="assigned_staff",
        overlaps="orders,user",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role in {"super_admin", "admin"}

    @property
    def is_staff(self):
        return self.role in {"super_admin", "admin", "staff"}


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    image_url = db.Column(db.String(255), default="")
    products = db.relationship("Product", back_populates="category")


class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    sku = db.Column(db.String(60), unique=True, nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    cost = db.Column(db.Numeric(10, 2), default=0)  # for profit calculation
    stock = db.Column(db.Integer, default=0, nullable=False)
    low_stock_threshold = db.Column(db.Integer, default=5, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    image_url = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship("Category", back_populates="products")
    variants = db.relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    tags = db.relationship("Tag", secondary=product_tags, lazy="subquery")

    @property
    def is_in_stock(self):
        return self.stock > 0

    @property
    def profit_margin(self):
        if float(self.price) > 0 and float(self.cost) > 0:
            return float(self.price) - float(self.cost)
        return 0


class ProductVariant(db.Model):
    __tablename__ = "product_variants"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    size = db.Column(db.String(20), nullable=False)
    color = db.Column(db.String(30), nullable=False)
    stock = db.Column(db.Integer, default=0, nullable=False)

    product = db.relationship("Product", back_populates="variants")


class CustomerProfile(db.Model):
    __tablename__ = "customer_profiles"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    address = db.Column(db.String(255), default="")
    phone = db.Column(db.String(30), default="")
    tags = db.Column(db.String(120), default="new")

    user = db.relationship("User", back_populates="profile")


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="pending")
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="orders", foreign_keys=[user_id])
    assigned_staff = db.relationship(
        "User",
        foreign_keys=[assigned_staff_id],
        back_populates="assigned_orders",
        overlaps="orders,user",
    )
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    invoice = db.relationship("Invoice", back_populates="order", uselist=False)


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    product_name = db.Column(db.String(150), nullable=False)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product")


class Invoice(db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), unique=True, nullable=False)
    invoice_number = db.Column(db.String(30), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pdf_path = db.Column(db.String(255))

    order = db.relationship("Order", back_populates="invoice")


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(30), default="info", nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

