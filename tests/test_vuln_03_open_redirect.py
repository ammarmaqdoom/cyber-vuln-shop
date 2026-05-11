def test_login_ignores_external_next_redirect(client):
    response = client.post(
        '/auth/login?next=https://evil.example/phish',
        data={'username': 'alice', 'password': 'Alice1234!'},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers['Location'] == '/products/'
    assert 'evil.example' not in response.headers['Location']


def test_login_allows_same_host_next_redirect(client):
    response = client.post(
        '/auth/login?next=/profile',
        data={'username': 'alice', 'password': 'Alice1234!'},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers['Location'] == '/profile'
