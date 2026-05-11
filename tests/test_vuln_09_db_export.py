def test_unauthenticated_database_export_endpoint_is_absent(client):
    response = client.get('/api/export')

    assert response.status_code == 404
    assert b'users' not in response.data
    assert b'orders' not in response.data
    assert b'password_hash' not in response.data


def test_export_route_is_not_registered_in_url_map(app):
    registered_routes = {rule.rule for rule in app.url_map.iter_rules()}

    assert '/api/export' not in registered_routes
