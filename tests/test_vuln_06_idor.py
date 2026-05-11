from conftest import login
from models import Order, User


def test_order_history_only_lists_current_users_orders(app, client):
    with app.app_context():
        alice_id = User.query.filter_by(username='alice').one().id
        bob_id = User.query.filter_by(username='bob').one().id
        alice_order_id = Order.query.filter_by(user_id=alice_id).one().id
        bob_order_id = Order.query.filter_by(user_id=bob_id).one().id

    login(client, 'alice', 'Alice1234!')

    response = client.get('/orders')

    assert response.status_code == 200
    assert f'Order #{alice_order_id}'.encode() in response.data
    assert f'Order #{bob_order_id}'.encode() not in response.data


def test_cross_user_order_detail_route_is_not_exposed(app, client):
    with app.app_context():
        bob_id = User.query.filter_by(username='bob').one().id
        bob_order_id = Order.query.filter_by(user_id=bob_id).one().id

    login(client, 'alice', 'Alice1234!')

    response = client.get(f'/orders/{bob_order_id}')

    assert response.status_code == 404
