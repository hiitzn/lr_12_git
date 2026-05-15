# ==================== test_endpoints.py ====================
import pytest
from datetime import datetime, timedelta


class TestAuthEndpoints:
    def test_login_page_get(self, client):
        response = client.get("/pages/login")
        assert response.status_code == 200
        assert "Вход" in response.text

    def test_login_success_waiter(self, client, test_user_waiter):
        response = client.post("/pages/login", data={"username": "waiter1", "password": "pass123"}, follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/pages/menu"
        assert "access_token" in response.cookies

    def test_login_success_cook(self, client, test_user_cook):
        response = client.post("/pages/login", data={"username": "cook1", "password": "pass123"}, follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/pages/kitchen"

    def test_login_failure(self, client):
        response = client.post("/pages/login", data={"username": "wrong", "password": "wrong"})
        assert response.status_code == 200
        assert "Неверное имя пользователя или пароль" in response.text

    def test_register_success(self, client, db_session):
        response = client.post("/pages/register", data={"username": "newwaiter", "password": "pass123"}, follow_redirects=False)
        assert response.status_code == 302
        assert "success=Регистрация+успешна" in response.headers["location"]

    def test_register_duplicate(self, client, test_user_waiter):
        response = client.post("/pages/register", data={"username": test_user_waiter.username, "password": "pass"}, follow_redirects=False)
        # Декоратор handle_errors редиректит с ошибкой
        assert response.status_code == 302
        assert "error" in response.headers["location"]

    def test_logout(self, client, test_user_waiter):
        client.post("/pages/login", data={"username": "waiter1", "password": "pass123"})
        response = client.get("/pages/logout", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/pages/login"
        # Кука должна быть удалена (значение None или пустая строка)
        assert response.cookies.get("access_token") == ""


class TestMenuEndpoints:
    def test_menu_list_authenticated_waiter(self, client, test_user_waiter):
        client.post("/pages/login", data={"username": "waiter1", "password": "pass123"})
        response = client.get("/pages/menu")
        assert response.status_code == 200
        assert "Меню" in response.text

    def test_menu_create_form_admin(self, client, test_user_admin):
        client.post("/pages/login", data={"username": "admin1", "password": "admin123"})
        response = client.get("/pages/menu/create")
        assert response.status_code == 200

    def test_menu_create_form_waiter_forbidden(self, client, test_user_waiter):
        client.post("/pages/login", data={"username": "waiter1", "password": "pass123"})
        response = client.get("/pages/menu/create")
        assert response.status_code == 403

    def test_menu_create_post_admin(self, client, test_user_admin):
        client.post("/pages/login", data={"username": "admin1", "password": "admin123"})
        response = client.post("/pages/menu/create", data={
            "name": "Test Dish", "price": 10.5, "category": "Test", "ingredients": "test", "instructions": "test", "cooking_time": 30
        }, follow_redirects=False)
        assert response.status_code == 302
        assert "success=Блюдо+добавлено" in response.headers["location"]


class TestOrderEndpoints:
    def test_create_order_post(self, client, test_user_waiter, test_table, test_menu_item):
        client.post("/pages/login", data={"username": "waiter1", "password": "pass123"})
        form_data = {
            "table_id": str(test_table.id),
            "notes": "Test",
            f"item_{test_menu_item.id}": "1",
            f"quantity_{test_menu_item.id}": "2"
        }
        response = client.post("/pages/orders/create", data=form_data, follow_redirects=False)
        assert response.status_code == 302
        assert "success=Заказ+создан" in response.headers["location"]


class TestKitchenEndpoints:
    def test_kitchen_page_cook(self, client, test_user_cook, test_order):
        client.post("/pages/login", data={"username": "cook1", "password": "pass123"})
        response = client.get("/pages/kitchen")
        assert response.status_code == 200
        assert "Активные заказы" in response.text

    def test_kitchen_waiter_forbidden(self, client, test_user_waiter):
        client.post("/pages/login", data={"username": "waiter1", "password": "pass123"})
        response = client.get("/pages/kitchen")
        assert response.status_code == 403


class TestAdminEndpoints:
    def test_admin_panel_admin(self, client, test_user_admin):
        client.post("/pages/login", data={"username": "admin1", "password": "admin123"})
        response = client.get("/pages/admin")
        assert response.status_code == 200
        assert "Админ-панель" in response.text