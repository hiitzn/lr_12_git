from app.tests.conftest import client


def test_register():
    response = client.post(
        "/auth/register",
        json={
            "username": "test_user",
            "password": "123456"
        }
    )

    assert response.status_code == 200
    assert response.json()["username"] == "test_user"


def test_login():
    response = client.post(
        "/auth/login",
        json={
            "username": "test_user",
            "password": "123456"
        }
    )

    assert response.status_code == 200
    assert "access_token" in response.cookies


def test_logout():
    response = client.post("/auth/logout")

    assert response.status_code == 200