from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from app.models import db, User, Product, Order

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin')
@login_required
@admin_required
def dashboard():
    user_count = User.query.count()
    product_count = Product.query.count()
    order_count = Order.query.count()
    return render_template('admin/dashboard.html', users=user_count, products=product_count, orders=order_count)

@admin_bp.route('/admin/users')
@login_required
@admin_required
def manage_users():
    return render_template('admin/users.html', users=User.query.all())

@admin_bp.route('/admin/products')
@login_required
@admin_required
def manage_products():
    return render_template('admin/products.html', products=Product.query.all())

@admin_bp.route('/admin/orders')
@login_required
@admin_required
def manage_orders():
    return render_template('admin/orders.html', orders=Order.query.all())