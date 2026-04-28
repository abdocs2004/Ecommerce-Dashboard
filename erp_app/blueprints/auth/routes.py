from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ...extensions import db
from ...models import CustomerProfile, User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Welcome back", "success")
            if user.is_staff:
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("products.catalog"))

        flash("Invalid email or password", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required", "warning")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(email=email).first():
            flash("Email already exists", "warning")
            return redirect(url_for("auth.register"))

        user = User(name=name, email=email, role="customer")
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        db.session.add(CustomerProfile(user_id=user.id, tags="new"))
        db.session.commit()

        flash("Account created successfully. Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.name = request.form.get("name", current_user.name).strip()
        current_user.gender = request.form.get("gender", current_user.gender)

        profile = current_user.profile
        if not profile:
            profile = CustomerProfile(user_id=current_user.id)
            db.session.add(profile)

        profile.phone = request.form.get("phone", "").strip()
        profile.address = request.form.get("address", "").strip()
        db.session.commit()
        flash("Profile updated successfully", "success")
        return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html", user=current_user)

