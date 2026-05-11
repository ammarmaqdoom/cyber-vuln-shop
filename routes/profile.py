import os
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models import Order, User

profile_bp = Blueprint('profile', __name__)
USERNAME_RE = re.compile(r'^[A-Za-z0-9_]{3,30}$')
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@profile_bp.route('/profile')
@login_required
def view_profile():
    return render_template('profile/view.html', user=current_user)

@profile_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip().lower()

    if not USERNAME_RE.match(username):
        flash('Username must be 3-30 characters and use only letters, numbers, or underscores.', 'danger')
        return redirect(url_for('profile.view_profile'))
    if not EMAIL_RE.match(email):
        flash('Enter a valid email address.', 'danger')
        return redirect(url_for('profile.view_profile'))
    duplicate = User.query.filter(
        User.id != current_user.id,
        ((User.username == username) | (User.email == email)),
    ).first()
    if duplicate:
        flash('Username or email is already in use.', 'warning')
        return redirect(url_for('profile.view_profile'))

    current_user.username = username
    current_user.email = email
    db.session.commit()
    flash('Profile updated successfully', 'success')
    return redirect(url_for('profile.view_profile'))

@profile_bp.route('/profile/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('profile.view_profile'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('profile.view_profile'))
    if file and allowed_file(file.filename):
        filename = f'user-{current_user.id}-{secure_filename(file.filename)}'
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        current_user.avatar = filename
        db.session.commit()
        flash('File uploaded successfully (validated)', 'success')
        return redirect(url_for('profile.view_profile'))
    else:
        allowed = ', '.join(sorted(current_app.config['ALLOWED_EXTENSIONS']))
        flash(f'Invalid file type. Allowed: {allowed}', 'danger')
        return redirect(url_for('profile.view_profile'))

@profile_bp.route('/orders')
@login_required
def order_history():
    # SECURE: Only returns current user's orders
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('profile/orders.html', orders=orders)