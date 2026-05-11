from models import User


def test_profile_update_without_csrf_token_is_rejected(csrf_app, csrf_client):
    with csrf_app.app_context():
        alice_id = User.query.filter_by(username='alice').one().id

    with csrf_client.session_transaction() as session:
        session['_user_id'] = str(alice_id)
        session['_fresh'] = True

    response = csrf_client.post(
        '/profile/update',
        data={'username': 'alice_changed', 'email': 'alice_changed@example.com'},
    )

    assert response.status_code == 400
    assert b'CSRF' in response.data

    with csrf_app.app_context():
        alice = User.query.get(alice_id)
        assert alice.username == 'alice'
        assert alice.email == 'alice@example.com'
