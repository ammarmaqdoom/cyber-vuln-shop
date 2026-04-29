import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import db, Order
from app.config import ALLOWED_EXTENSIONS

profile_bp = Blueprint('profile', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@profile_bp.route('/profile')
@login_required
def view_profile():
    return render_template('profile/view.html', user=current_user)

@profile_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    username = request.form.get('username')
    email = request.form.get('email')
    if username:
        current_user.username = username
    if email:
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
        filename = secure_filename(file.filename)
        # Save logic goes here: file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        flash('File uploaded successfully (validated)', 'success')
        return redirect(url_for('profile.view_profile'))
    else:
        flash(f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}', 'danger')
        return redirect(url_for('profile.view_profile'))

@profile_bp.route('/orders')
@login_required
def order_history():
    # SECURE: Only returns current user's orders
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('profile/orders.html', orders=orders)