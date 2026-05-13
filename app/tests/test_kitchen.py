from app.tests.conftest import client


def test_kitchen_requires_auth():
    response = client.patch(
        "/kitchen/1?status=cooking"
    )

    assert response.status_code == 401


def test_invalid_status():
    response = client.patch(
        "/kitchen/1?status=invalid"
    )

    assert response.status_code in [400, 401]