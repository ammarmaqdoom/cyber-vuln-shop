from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Cart, CartItem, Order, OrderItem, Product
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
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()

    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()
    if cart_item:
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
    new_qty = int(request.form.get('quantity', 1))
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
        return redirect(url_for('products.list'))

    items = CartItem.query.filter_by(cart_id=cart.id).all()
    if not items:
        flash('Cart is empty', 'warning')
        return redirect(url_for('products.list'))

    order = Order(user_id=current_user.id, created_at=datetime.utcnow())
    db.session.add(order)
    db.session.flush()

    for item in items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.product.price
        )
        db.session.add(order_item)

    CartItem.query.filter_by(cart_id=cart.id).delete()
    db.session.commit()
    flash('Order placed successfully!', 'success')
    return redirect(url_for('profile.order_history'))