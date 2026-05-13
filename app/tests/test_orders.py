from app.tests.conftest import client


def test_get_orders_unauthorized():
    response = client.get("/orders/")

    assert response.status_code == 401


def test_delete_nonexistent_order():
    response = client.delete("/orders/999")

    assert response.status_code in [401, 404]