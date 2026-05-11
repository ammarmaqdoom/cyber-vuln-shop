from conftest import login


def test_non_admin_user_is_redirected_from_admin_dashboard(client):
    login(client, 'alice', 'Alice1234!')

    response = client.get('/admin', follow_redirects=False)

    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']


def test_admin_user_can_access_admin_dashboard(client):
    login(client, 'admin', 'Admin1234!')

    response = client.get('/admin')

    assert response.status_code == 200
    assert b'Admin Dashboard' in response.data
