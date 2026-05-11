from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Cart, CartItem, Order, OrderItem, Product
from datetime import datetime

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('/cart')
@login_required
def view_cart():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
    items = CartItem.query.filter_by(cart_id=cart.id).all()
    total = sum(item.quantity * item.product.price for item in items)
    return render_template('cart/view.html', items=items, total=total)

@cart_bp.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    if product.stock < 1:
        flash('This product is out of stock.', 'warning')
        return redirect(url_for('products.product_detail', product_id=product.id))

    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()

    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()
    if cart_item:
        if cart_item.quantity + 1 > product.stock:
            flash('Not enough stock available.', 'warning')
            return redirect(url_for('cart.view_cart'))
        cart_item.quantity += 1
    else:
        cart_item = CartItem(cart_id=cart.id, product_id=product.id, quantity=1)
        db.session.add(cart_item)
    db.session.commit()
    flash('Item added to cart', 'success')
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/cart/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.cart.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('cart.view_cart'))
    db.session.delete(item)
    db.session.commit()
    flash('Item removed', 'success')
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def update_quantity(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.cart.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('cart.view_cart'))
    try:
        new_qty = int(request.form.get('quantity', 1))
    except ValueError:
        flash('Quantity must be a valid number.', 'danger')
        return redirect(url_for('cart.view_cart'))
    if new_qty > item.product.stock:
        flash('Requested quantity exceeds available stock.', 'warning')
        return redirect(url_for('cart.view_cart'))
    if new_qty > 0:
        item.quantity = new_qty
    else:
        db.session.delete(item)
    db.session.commit()
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        flash('Cart is empty', 'warning')
        return redirect(url_for('products.list_products'))

    items = CartItem.query.filter_by(cart_id=cart.id).all()
    if not items:
        flash('Cart is empty', 'warning')
        return redirect(url_for('products.list_products'))

    for item in items:
        if item.quantity > item.product.stock:
            flash(f'Not enough stock for {item.product.name}.', 'warning')
            return redirect(url_for('cart.view_cart'))

    total = sum(item.quantity * item.product.price for item in items)
    order = Order(user_id=current_user.id, total=total, status='paid', created_at=datetime.utcnow())
    db.session.add(order)
    db.session.flush()

    for item in items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.product.price
        )
        item.product.stock -= item.quantity
        db.session.add(order_item)

    CartItem.query.filter_by(cart_id=cart.id).delete()
    db.session.commit()
    flash('Order placed successfully!', 'success')
    return redirect(url_for('profile.order_history'))