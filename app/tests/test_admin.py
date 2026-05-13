from app.tests.conftest import client


def test_admin_routes_protected():
    response = client.get("/analytics/")

    assert response.status_code in [401, 403]


def test_change_role_protected():
    response = client.patch(
        "/admin/users/1/role?role=admin"
    )

    assert response.status_code in [401, 403]