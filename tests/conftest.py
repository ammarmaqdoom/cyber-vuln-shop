import bcrypt
import pytest

from app import create_app
from config import Config
from extensions import db
from models import Order, OrderItem, Product, User


class SecurityTestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret'


@pytest.fixture()
def app(tmp_path):
    class TmpConfig(SecurityTestConfig):
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{tmp_path / "security-test.db"}'
        UPLOAD_FOLDER = str(tmp_path / 'uploads')

    test_app = create_app(TmpConfig)
    _seed_database(test_app)
    return test_app


@pytest.fixture()
def csrf_app(tmp_path):
    class TmpConfig(SecurityTestConfig):
        WTF_CSRF_ENABLED = True
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{tmp_path / "csrf-security-test.db"}'
        UPLOAD_FOLDER = str(tmp_path / 'uploads')

    test_app = create_app(TmpConfig)
    _seed_database(test_app)
    return test_app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def csrf_client(csrf_app):
    return csrf_app.test_client()


def login(client, username='alice', password='Alice1234!', follow_redirects=True):
    return client.post(
        '/auth/login',
        data={'username': username, 'password': password},
        follow_redirects=follow_redirects,
    )


def _hash(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _seed_database(test_app):
    with test_app.app_context():
        db.drop_all()
        db.create_all()

        admin = User(username='admin', email='admin@example.com', password_hash=_hash('Admin1234!'), role='admin')
        alice = User(username='alice', email='alice@example.com', password_hash=_hash('Alice1234!'), role='user')
        bob = User(username='bob', email='bob@example.com', password_hash=_hash('Bob1234!'), role='user')
        mouse = Product(name='Mouse', description='Wireless mouse', price=10.0, stock=5, category='Electronics')
        keyboard = Product(name='Keyboard', description='Mechanical keyboard', price=25.0, stock=3, category='Electronics')

        db.session.add_all([admin, alice, bob, mouse, keyboard])
        db.session.flush()

        alice_order = Order(user_id=alice.id, total=10.0, status='paid')
        bob_order = Order(user_id=bob.id, total=25.0, status='pending')
        db.session.add_all([alice_order, bob_order])
        db.session.flush()

        db.session.add_all(
            [
                OrderItem(order_id=alice_order.id, product_id=mouse.id, quantity=1, unit_price=mouse.price),
                OrderItem(order_id=bob_order.id, product_id=keyboard.id, quantity=1, unit_price=keyboard.price),
            ]
        )
        db.session.commit()
