from conftest import login


def test_unauthenticated_user_dump_endpoint_is_absent(client):
    response = client.get('/api/admin/users')

    assert response.status_code == 404
    assert b'password_hash' not in response.data
    assert b'weak_password_hash' not in response.data


def test_admin_user_management_requires_admin_role(client):
    unauthenticated = client.get('/admin/users', follow_redirects=False)
    assert unauthenticated.status_code == 302
    assert '/auth/login' in unauthenticated.headers['Location']

    login(client, 'alice', 'Alice1234!')
    non_admin = client.get('/admin/users', follow_redirects=False)

    assert non_admin.status_code == 302
    assert '/auth/login' in non_admin.headers['Location']
