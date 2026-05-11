from conftest import login


def test_review_script_payload_is_escaped_on_product_detail(client):
    login(client, 'alice', 'Alice1234!')

    payload = '<script>alert(1)</script>'
    post_response = client.post(
        '/products/1/reviews',
        data={'rating': '5', 'text': payload},
        follow_redirects=False,
    )
    assert post_response.status_code == 302

    response = client.get('/products/1')

    assert response.status_code == 200
    assert payload.encode() not in response.data
    assert b'&lt;script&gt;alert(1)&lt;/script&gt;' in response.data
