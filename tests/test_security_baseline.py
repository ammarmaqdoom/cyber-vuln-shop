import bcrypt
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from config import Config
from extensions import db
from models import Order, Product, User


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret'


@pytest.fixture()
def app(tmp_path):
    class TmpConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{tmp_path / "test.db"}'

    app = create_app(TmpConfig)
    with app.app_context():
        db.drop_all()
        db.create_all()
        db.session.add_all(
            [
                User(username='admin', email='admin@example.com', password_hash=_hash('Admin1234!'), role='admin'),
                User(username='alice', email='alice@example.com', password_hash=_hash('Alice1234!'), role='user'),
                Product(name='Mouse', description='Wireless mouse', price=10.0, stock=5, category='Electronics'),
            ]
        )
        db.session.commit()
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_non_admin_cannot_access_admin_dashboard(client):
    _login(client, 'alice', 'Alice1234!')
    response = client.get('/admin', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']


def test_admin_can_access_admin_dashboard(client):
    _login(client, 'admin', 'Admin1234!')
    response = client.get('/admin')
    assert response.status_code == 200
    assert b'Admin Dashboard' in response.data


def test_product_search_and_checkout_flow(client, app):
    _login(client, 'alice', 'Alice1234!')
    assert b'Mouse' in client.get('/products/?q=mouse').data

    client.post('/cart/add/1')
    response = client.post('/checkout', follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        order = Order.query.filter_by(user_id=2).one()
        assert order.total == 10.0
        assert order.items[0].unit_price == 10.0


def _hash(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _login(client, username, password):
    return client.post('/auth/login', data={'username': username, 'password': password}, follow_redirects=True)
