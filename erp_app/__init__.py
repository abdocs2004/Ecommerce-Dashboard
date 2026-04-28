from flask import Flask, redirect, url_for
from flask_login import current_user

from .config import Config
from .extensions import db, login_manager, mail, migrate
from .models import Category, CustomerProfile, User


def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    from .blueprints.auth.routes import auth_bp
    from .blueprints.admin.routes import admin_bp
    from .blueprints.products.routes import products_bp
    from .blueprints.orders.routes import orders_bp
    from .blueprints.crm.routes import crm_bp
    from .blueprints.inventory.routes import inventory_bp
    from .blueprints.reports.routes import reports_bp
    from .blueprints.api.routes import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(products_bp, url_prefix="/products")
    app.register_blueprint(orders_bp, url_prefix="/orders")
    app.register_blueprint(crm_bp, url_prefix="/crm")
    app.register_blueprint(inventory_bp, url_prefix="/inventory")
    app.register_blueprint(reports_bp, url_prefix="/reports")
    app.register_blueprint(api_bp)

    @app.route("/")
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if current_user.is_staff:
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("products.catalog"))

    with app.app_context():
        db.create_all()
        seed_defaults()

    return app


def seed_defaults():
    if not Category.query.first():
        default_categories = [
            ("Clothing", "fashion"),
            ("Electronics", "electronics"),
            ("Home", "home"),
            ("Beauty", "beauty"),
            ("Shoes", "shoes"),
            ("Books", "books"),
        ]
        for name, img in default_categories:
            db.session.add(Category(name=name, image_url=f"categories/{img}.png"))

    if not User.query.filter_by(email="superadmin@erp.local").first():
        user = User(name="Super Admin", email="superadmin@erp.local", role="super_admin")
        user.set_password("admin123")
        db.session.add(user)
        db.session.flush()
        db.session.add(CustomerProfile(user_id=user.id, tags="vip"))

    if not User.query.filter_by(email="admin@erp.local").first():
        user = User(name="Admin", email="admin@erp.local", role="admin")
        user.set_password("admin123")
        db.session.add(user)
        db.session.flush()
        db.session.add(CustomerProfile(user_id=user.id, tags="admin"))

    if not User.query.filter_by(email="staff@erp.local").first():
        user = User(name="Staff", email="staff@erp.local", role="staff")
        user.set_password("staff123")
        db.session.add(user)
        db.session.flush()
        db.session.add(CustomerProfile(user_id=user.id, tags="staff"))

    db.session.commit()

