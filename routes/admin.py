from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user

from extensions import db
from models import Order, Product, User

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
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


@admin_bp.route('/admin/users/<int:user_id>/role', methods=['POST'])
@login_required
@admin_required
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    role = request.form.get('role', 'user')
    if role not in {'user', 'admin'}:
        flash('Invalid role selected.', 'danger')
        return redirect(url_for('admin.manage_users'))
    if user.id == current_user.id and role != 'admin':
        flash('You cannot remove your own admin role.', 'warning')
        return redirect(url_for('admin.manage_users'))
    user.role = role
    db.session.commit()
    flash('User role updated.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/admin/products')
@login_required
@admin_required
def manage_products():
    return render_template('admin/products.html', products=Product.query.all())


@admin_bp.route('/admin/products/new', methods=['POST'])
@login_required
@admin_required
def create_product():
    product = _product_from_form(Product())
    if product is None:
        return redirect(url_for('admin.manage_products'))

    db.session.add(product)
    db.session.commit()
    flash('Product created.', 'success')
    return redirect(url_for('admin.manage_products'))


@admin_bp.route('/admin/products/<int:product_id>/edit', methods=['POST'])
@login_required
@admin_required
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    updated = _product_from_form(product)
    if updated is None:
        return redirect(url_for('admin.manage_products'))

    db.session.commit()
    flash('Product updated.', 'success')
    return redirect(url_for('admin.manage_products'))


@admin_bp.route('/admin/products/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted.', 'success')
    return redirect(url_for('admin.manage_products'))

@admin_bp.route('/admin/orders')
@login_required
@admin_required
def manage_orders():
    return render_template('admin/orders.html', orders=Order.query.all())


@admin_bp.route('/admin/orders/<int:order_id>/status', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    status = request.form.get('status', 'pending')
    if status not in {'pending', 'paid', 'shipped', 'delivered', 'cancelled'}:
        flash('Invalid order status.', 'danger')
        return redirect(url_for('admin.manage_orders'))
    order.status = status
    db.session.commit()
    flash('Order status updated.', 'success')
    return redirect(url_for('admin.manage_orders'))


def _product_from_form(product):
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', '').strip() or 'General'
    image_url = request.form.get('image_url', '').strip() or 'placeholder.png'

    try:
        price = float(request.form.get('price', ''))
        stock = int(request.form.get('stock', ''))
    except ValueError:
        flash('Price must be a number and stock must be an integer.', 'danger')
        return None

    if not name or not description:
        flash('Product name and description are required.', 'danger')
        return None
    if price < 0 or stock < 0:
        flash('Price and stock cannot be negative.', 'danger')
        return None

    product.name = name
    product.description = description
    product.category = category
    product.price = price
    product.stock = stock
    product.image_url = image_url
    return product