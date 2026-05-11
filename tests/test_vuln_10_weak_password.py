from models import User


def test_registration_rejects_short_weak_password(app, client):
    response = client.post(
        '/auth/register',
        data={
            'username': 'weakuser',
            'email': 'weakuser@example.com',
            'password': '123',
        },
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert b'Password must be at least 8 characters.' in response.data

    with app.app_context():
        assert User.query.filter_by(username='weakuser').first() is None


def test_registration_accepts_password_that_meets_minimum_policy(app, client):
    response = client.post(
        '/auth/register',
        data={
            'username': 'stronguser',
            'email': 'stronguser@example.com',
            'password': 'Strong123!',
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'

    with app.app_context():
        assert User.query.filter_by(username='stronguser').one()
