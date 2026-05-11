"""Intentionally vulnerable demo of Cyber Vuln Shop.

Run on port 5001 alongside the fixed app on 5000 so we can demonstrate
each vulnerability and then show the remediation in the production code.

Do NOT expose this server outside of the demo environment.
"""

import hashlib
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

import bcrypt
from flask import (
    Flask,
    Response,
    flash,
    jsonify,
    redirect,
    render_template_string,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_, text

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import Config
from extensions import db, login_manager
from models import Order, OrderItem, Product, Review, User


class VulnerableDemoConfig(Config):
    SECRET_KEY = os.environ.get("SECRET_KEY", "vulnerable-demo-secret")
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    DEBUG = True
    EXPOSED_ADMIN_API_KEY = "demo-admin-api-key-do-not-use"
    LLM_API_KEY = "sk-demo-llm-key-leaked-for-training"
    JWT_SECRET = "weak-demo-jwt-secret"


def create_vulnerable_app():
    app = Flask(__name__)
    app.config.from_object(VulnerableDemoConfig)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"

    with app.app_context():
        db.create_all()

    @app.route("/")
    def index():
        return redirect(url_for("login"))

    # ──────────────────────────────────────────────────────────────────────
    # Vulnerability 1: weak password registration (no policy)
    # Vulnerability 2: passwords stored with weak hash next to bcrypt copy
    # ──────────────────────────────────────────────────────────────────────
    @app.route("/auth/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            if not username or not email or not password:
                flash("Username, email, and password are required.", "danger")
                return render_template_string(REGISTER_TEMPLATE)

            existing = User.query.filter(
                or_(User.username == username, User.email == email)
            ).first()
            if existing:
                flash("Username or email already exists.", "warning")
                return render_template_string(REGISTER_TEMPLATE)

            # VULNERABLE: no minimum length, no complexity check.
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

            # VULNERABLE: also store a weak MD5 mirror used by the legacy "API".
            weak_hash = hashlib.md5(password.encode()).hexdigest()
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                avatar=weak_hash,
            )
            db.session.add(user)
            db.session.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))

        return render_template_string(REGISTER_TEMPLATE)

    # ──────────────────────────────────────────────────────────────────────
    # Vulnerability 3: missing rate limiting / lockout in vulnerable login
    # Vulnerability 4: open redirect on `next` parameter
    # Vulnerability 5: missing CSRF protection on POST forms
    # ──────────────────────────────────────────────────────────────────────
    @app.route("/auth/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username_or_email = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = User.query.filter(
                or_(
                    User.username == username_or_email,
                    User.email == username_or_email.lower(),
                )
            ).first()

            if not user or not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
                # VULNERABLE: no failed-attempt counter and no lockout.
                flash("Invalid credentials.", "danger")
                return render_template_string(LOGIN_TEMPLATE)

            login_user(user)

            # VULNERABLE: untrusted redirect target is used directly.
            return redirect(request.args.get("next") or url_for("products"))

        return render_template_string(LOGIN_TEMPLATE)

    @app.route("/auth/logout", methods=["GET", "POST"])
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))

    # ──────────────────────────────────────────────────────────────────────
    # Vulnerability 6: SQL injection in product search via raw SQL.
    # ──────────────────────────────────────────────────────────────────────
    @app.route("/products/")
    @login_required
    def products():
        q = request.args.get("q", "")
        try:
            # VULNERABLE: query parameter is concatenated into raw SQL.
            sql = (
                "SELECT id, name, description, price, stock, category, image_url "
                "FROM products WHERE name LIKE '%"
                + q
                + "%' OR description LIKE '%"
                + q
                + "%' ORDER BY id DESC"
            )
            rows = db.session.execute(text(sql)).fetchall()
            error = None
        except Exception as exc:  # noqa: BLE001 — demo only
            rows = []
            error = str(exc)
        items = [dict(row._mapping) for row in rows]
        return render_template_string(
            PRODUCTS_TEMPLATE, products=items, q=q, error=error
        )

    # ──────────────────────────────────────────────────────────────────────
    # Vulnerability 7: stored XSS in product review text.
    # ──────────────────────────────────────────────────────────────────────
    @app.route("/products/<int:product_id>", methods=["GET", "POST"])
    @login_required
    def product_detail(product_id):
        product = Product.query.get_or_404(product_id)
        if request.method == "POST":
            text_value = request.form.get("text", "")
            rating_value = request.form.get("rating", "5")
            try:
                rating = int(rating_value)
            except ValueError:
                rating = 5
            db.session.add(
                Review(
                    user_id=current_user.id,
                    product_id=product.id,
                    text=text_value,
                    rating=max(1, min(5, rating)),
                )
            )
            db.session.commit()
            return redirect(url_for("product_detail", product_id=product.id))
        reviews = Review.query.filter_by(product_id=product.id).order_by(Review.created_at.desc()).all()
        return render_template_string(
            PRODUCT_DETAIL_TEMPLATE, product=product, reviews=reviews
        )

    # ──────────────────────────────────────────────────────────────────────
    # Vulnerability 8: IDOR — any logged-in user can read any order by ID.
    # ──────────────────────────────────────────────────────────────────────
    @app.route("/orders/<int:order_id>")
    @login_required
    def view_order(order_id):
        order = Order.query.get_or_404(order_id)
        items = OrderItem.query.filter_by(order_id=order.id).all()
        return render_template_string(
            ORDER_TEMPLATE, order=order, items=items, current=current_user
        )

    # ──────────────────────────────────────────────────────────────────────
    # Vulnerability 9: broken RBAC — any authenticated user reaches admin.
    # ──────────────────────────────────────────────────────────────────────
    @app.route("/admin")
    @login_required
    def admin_dashboard():
        return render_template_string(
            ADMIN_TEMPLATE,
            users=User.query.all(),
            products=Product.query.all(),
            orders=Order.query.all(),
        )

    # ──────────────────────────────────────────────────────────────────────
    # Vulnerability 10: unauthenticated user list with weak password hashes.
    # ──────────────────────────────────────────────────────────────────────
    @app.route("/api/admin/users")
    def api_admin_users():
        users = User.query.all()
        # VULNERABLE: no auth check, returns sensitive hashes (avatar holds MD5).
        return jsonify(
            [
                {
                    "id": u.id,
                    "username": u.username,
                    "email": u.email,
                    "role": u.role,
                    "weak_password_hash": u.avatar,
                    "bcrypt_password_hash": u.password_hash,
                }
                for u in users
            ]
        )

    # ──────────────────────────────────────────────────────────────────────
    # Vulnerability 11: debug endpoint leaks secrets and environment.
    # ──────────────────────────────────────────────────────────────────────
    @app.route("/debug")
    def debug_endpoint():
        secrets = {
            "SECRET_KEY": app.config.get("SECRET_KEY"),
            "EXPOSED_ADMIN_API_KEY": app.config.get("EXPOSED_ADMIN_API_KEY"),
            "LLM_API_KEY": app.config.get("LLM_API_KEY"),
            "JWT_SECRET": app.config.get("JWT_SECRET"),
            "SQLALCHEMY_DATABASE_URI": app.config.get("SQLALCHEMY_DATABASE_URI"),
            "ENV": {k: v for k, v in os.environ.items() if "PATH" not in k.upper()},
        }
        return jsonify(secrets)

    # ──────────────────────────────────────────────────────────────────────
    # Vulnerability 12: unauthenticated bulk export of database via shell.
    # ──────────────────────────────────────────────────────────────────────
    @app.route("/api/export")
    def export_data():
        db_path = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        payload = {}
        for table in ("users", "products", "orders", "order_items", "reviews"):
            cursor = connection.execute(f"SELECT * FROM {table}")
            payload[table] = [dict(row) for row in cursor.fetchall()]
        connection.close()
        return jsonify(payload)

    @app.route("/profile")
    @login_required
    def profile():
        return render_template_string(PROFILE_TEMPLATE, user=current_user)

    @app.route("/profile/update", methods=["POST"])
    @login_required
    def profile_update():
        # VULNERABLE: no CSRF token and no input validation.
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        if username:
            current_user.username = username
        if email:
            current_user.email = email
        db.session.commit()
        return render_template_string(PROFILE_TEMPLATE, user=current_user, updated=True)

    # ──────────────────────────────────────────────────────────────────────
    # Vulnerability 13: verbose error pages reveal stack trace.
    # ──────────────────────────────────────────────────────────────────────
    @app.errorhandler(Exception)
    def handle_exception(exc):
        import traceback

        body = (
            "<h1>Server Error</h1><pre>"
            + traceback.format_exc()
            + "</pre>"
        )
        return Response(body, status=500, mimetype="text/html")

    return app


BASE_STYLE = """
<style>
body { font-family: Segoe UI, Arial, sans-serif; margin: 2rem; background: #f8fafc; color: #172033; }
.card { background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem; margin-bottom: 1rem; }
input, button, textarea { padding: .6rem; margin-top: .4rem; width: 100%; box-sizing: border-box; }
button { background: #dc2626; color: white; border: 0; border-radius: 6px; cursor: pointer; }
a { color: #2563eb; }
.danger { color: #b91c1c; font-weight: 700; }
nav.top a { margin-right: 12px; }
pre { white-space: pre-wrap; word-break: break-word; }
</style>
"""

LOGIN_TEMPLATE = BASE_STYLE + """
<div class="card">
  <h1>Vulnerable Demo Login</h1>
  <p class="danger">Intentionally vulnerable build for live attack demonstration.</p>
  <form method="post">
    <label>Username or Email</label>
    <input name="username" required>
    <label>Password</label>
    <input name="password" type="password" required>
    <button type="submit">Login</button>
  </form>
  <p>Demo users: admin/Admin1234!, alice/Alice1234!, bob/Bob1234!</p>
  <p><a href="/auth/register">Register</a></p>
</div>
"""

REGISTER_TEMPLATE = BASE_STYLE + """
<div class="card">
  <h1>Vulnerable Demo Register</h1>
  <form method="post">
    <label>Username</label>
    <input name="username" required>
    <label>Email</label>
    <input name="email" type="email" required>
    <label>Password (no policy enforced)</label>
    <input name="password" type="password" required>
    <button type="submit">Create account</button>
  </form>
</div>
"""

PRODUCTS_TEMPLATE = BASE_STYLE + """
<nav class="top">
  <a href="/products/">Products</a>
  <a href="/profile">Profile</a>
  <a href="/admin">Admin</a>
  <a href="/api/admin/users">User dump</a>
  <a href="/api/export">DB export</a>
  <a href="/debug">Debug</a>
  <a href="/auth/logout">Logout</a>
</nav>
<div class="card">
  <h1>Vulnerable Demo Products</h1>
  <form method="get" action="/products/">
    <input name="q" value="{{ q }}" placeholder="Search (SQLi enabled)">
    <button type="submit">Search</button>
  </form>
  {% if error %}<p class="danger">SQL error: {{ error }}</p>{% endif %}
  <ul>
    {% for product in products %}
      <li><a href="/products/{{ product.id }}">{{ product.name }}</a> — ${{ "%.2f"|format(product.price) }}</li>
    {% endfor %}
  </ul>
</div>
"""

PRODUCT_DETAIL_TEMPLATE = BASE_STYLE + """
<nav class="top"><a href="/products/">Back</a></nav>
<div class="card">
  <h1>{{ product.name }}</h1>
  <p>{{ product.description|safe }}</p>
  <h2>Reviews</h2>
  {% for review in reviews %}
    <div class="card">
      <strong>{{ review.author.username }}</strong> ({{ review.rating }}/5)
      <p>{{ review.text|safe }}</p>
    </div>
  {% else %}
    <p>No reviews yet.</p>
  {% endfor %}
  <h2>Add Review</h2>
  <form method="post">
    <label>Rating</label>
    <input name="rating" type="number" min="1" max="5" value="5">
    <label>Text (XSS not blocked)</label>
    <textarea name="text" rows="3"></textarea>
    <button type="submit">Submit</button>
  </form>
</div>
"""

ORDER_TEMPLATE = BASE_STYLE + """
<nav class="top"><a href="/products/">Back</a></nav>
<div class="card">
  <h1>Order #{{ order.id }}</h1>
  <p class="danger">Vulnerable demo allows any logged-in user to read this order via IDOR.</p>
  <p>Customer ID: {{ order.user_id }} (current user ID: {{ current.id }})</p>
  <p>Status: {{ order.status }}</p>
  <p>Total: ${{ "%.2f"|format(order.total) }}</p>
  <h2>Items</h2>
  <ul>
    {% for item in items %}
      <li>Product {{ item.product_id }} — qty {{ item.quantity }} @ ${{ "%.2f"|format(item.unit_price) }}</li>
    {% endfor %}
  </ul>
</div>
"""

ADMIN_TEMPLATE = BASE_STYLE + """
<nav class="top">
  <a href="/products/">Products</a>
  <a href="/api/admin/users">User dump</a>
  <a href="/api/export">DB export</a>
  <a href="/debug">Debug</a>
</nav>
<div class="card">
  <h1>Admin Dashboard - Vulnerable</h1>
  <p class="danger">This page is visible to any authenticated user in the vulnerable version.</p>
  <h2>Users</h2>
  <ul>
    {% for user in users %}
      <li>{{ user.username }} | {{ user.email }} | role={{ user.role }} | md5={{ user.avatar }}</li>
    {% endfor %}
  </ul>
  <h2>Products: {{ products|length }}</h2>
  <h2>Orders: {{ orders|length }}</h2>
</div>
"""

PROFILE_TEMPLATE = BASE_STYLE + """
<nav class="top"><a href="/products/">Back</a></nav>
<div class="card">
  <h1>Profile - Vulnerable</h1>
  {% if updated %}<p class="danger">Profile updated without CSRF protection.</p>{% endif %}
  <p>Current username: <strong>{{ user.username }}</strong></p>
  <p>Current email: <strong>{{ user.email }}</strong></p>
  <form method="post" action="/profile/update">
    <label>Username</label>
    <input name="username" value="{{ user.username }}">
    <label>Email</label>
    <input name="email" value="{{ user.email }}">
    <button type="submit">Update Profile</button>
  </form>
</div>
"""


if __name__ == "__main__":
    app = create_vulnerable_app()
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", 5001)),
        debug=False,
    )
