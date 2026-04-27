from datetime import datetime, timedelta

import bcrypt
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_

from extensions import db
from models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('auth.login'))

	if request.method == 'POST':
		username = request.form.get('username', '').strip()
		email = request.form.get('email', '').strip().lower()
		password = request.form.get('password', '')

		if not username or not email or not password:
			flash('Username, email, and password are required.', 'danger')
			return render_template('auth/register.html')

		existing_user = User.query.filter(
			or_(User.username == username, User.email == email)
		).first()
		if existing_user:
			flash('Username or email already exists.', 'warning')
			return render_template('auth/register.html')

		password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
		user = User(username=username, email=email, password_hash=password_hash)
		db.session.add(user)
		db.session.commit()

		flash('Registration successful. Please log in.', 'success')
		return redirect(url_for('auth.login'))

	return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return render_template('auth/login.html')

	if request.method == 'POST':
		username_or_email = request.form.get('username', '').strip()
		password = request.form.get('password', '')

		if not username_or_email or not password:
			flash('Username/email and password are required.', 'danger')
			return render_template('auth/login.html')

		user = User.query.filter(
			or_(User.username == username_or_email, User.email == username_or_email.lower())
		).first()

		if user and user.locked_until and user.locked_until > datetime.utcnow():
			remaining_minutes = int((user.locked_until - datetime.utcnow()).total_seconds() // 60) + 1
			flash(
				f'Account locked due to repeated failed logins. Try again in about {remaining_minutes} minutes.',
				'danger',
			)
			return render_template('auth/login.html')

		if not user or not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
			if user:
				user.failed_attempts = (user.failed_attempts or 0) + 1
				if user.failed_attempts >= 5:
					user.locked_until = datetime.utcnow() + timedelta(minutes=15)
					flash('Too many failed attempts. Account locked for 15 minutes.', 'danger')
				else:
					flash('Invalid credentials.', 'danger')
				db.session.commit()
			else:
				flash('Invalid credentials.', 'danger')
			return render_template('auth/login.html')

		user.failed_attempts = 0
		user.locked_until = None
		db.session.commit()

		login_user(user)
		flash('Logged in successfully.', 'success')
		next_url = request.args.get('next')
		return redirect(next_url or url_for('auth.login'))

	return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
	logout_user()
	flash('You have been logged out.', 'info')
	return redirect(url_for('auth.login'))
