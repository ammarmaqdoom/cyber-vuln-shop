from flask import Flask, redirect, url_for
from config import Config
from extensions import csrf, db, login_manager
import os

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    from routes.auth import auth_bp
    from routes.products import products_bp
    from routes.cart import cart_bp
    from routes.admin import admin_bp
    from routes.profile import profile_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(profile_bp)

    @app.route('/')
    def index():
        return redirect(url_for('products.list_products'))

    @app.route('/healthz')
    def healthz():
        return {'status': 'ok'}

    with app.app_context():
        import models  # noqa: F401 — registers models with SQLAlchemy
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host=os.environ.get('HOST', '127.0.0.1'), port=int(os.environ.get('PORT', 5000)), debug=False)
