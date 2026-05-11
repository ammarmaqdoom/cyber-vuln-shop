def test_debug_endpoint_is_not_registered(client):
    response = client.get('/debug')

    assert response.status_code == 404


def test_application_debug_mode_is_disabled(app):
    assert app.debug is False
