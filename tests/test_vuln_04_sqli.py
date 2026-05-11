from conftest import login


def test_product_search_treats_sql_payload_as_literal_input(client):
    login(client, 'alice', 'Alice1234!')

    payload = "%' UNION SELECT id, username, email, 0, 0, role, avatar FROM users --"
    response = client.get('/products/', query_string={'q': payload})

    assert response.status_code == 200
    assert b'alice@example.com' not in response.data
    assert b'admin@example.com' not in response.data
    assert b'OperationalError' not in response.data


def test_product_search_still_returns_matching_products(client):
    login(client, 'alice', 'Alice1234!')

    response = client.get('/products/', query_string={'q': 'mouse'})

    assert response.status_code == 200
    assert b'Mouse' in response.data
