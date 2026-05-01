from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from extensions import db
from models import Product, Review

products_bp = Blueprint('products', __name__, url_prefix='/products')


@products_bp.route('/')
def list_products():
	query = request.args.get('q', '').strip()
	products_query = Product.query

	if query:
		search_term = f'%{query}%'
		products_query = products_query.filter(
			or_(
				Product.name.ilike(search_term),
				Product.description.ilike(search_term),
				Product.category.ilike(search_term),
			)
		)

	products = products_query.order_by(Product.created_at.desc()).all()
	return render_template('products/list.html', products=products, q=query)


@products_bp.route('/<int:product_id>')
def product_detail(product_id):
	product = Product.query.get_or_404(product_id)
	reviews = Review.query.filter_by(product_id=product.id).order_by(Review.created_at.desc()).all()
	return render_template('products/detail.html', product=product, reviews=reviews)


@products_bp.route('/<int:product_id>/reviews', methods=['POST'])
@login_required
def add_review(product_id):
	product = Product.query.get_or_404(product_id)
	rating_raw = request.form.get('rating', '').strip()
	text = request.form.get('text', '').strip()

	try:
		rating = int(rating_raw)
	except ValueError:
		flash('Rating must be a number between 1 and 5.', 'danger')
		return redirect(url_for('products.product_detail', product_id=product.id))

	if rating < 1 or rating > 5:
		flash('Rating must be between 1 and 5.', 'danger')
		return redirect(url_for('products.product_detail', product_id=product.id))

	if not text:
		flash('Review text is required.', 'danger')
		return redirect(url_for('products.product_detail', product_id=product.id))

	review = Review(
		user_id=current_user.id,
		product_id=product.id,
		text=text,
		rating=rating,
	)
	db.session.add(review)
	db.session.commit()

	flash('Your review has been posted.', 'success')
	return redirect(url_for('products.product_detail', product_id=product.id))
