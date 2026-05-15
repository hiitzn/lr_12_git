# ==================== test_services.py ====================
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.services.auth_service import AuthService
from app.services.order_service import OrderService
from app.services.table_service import TableService
from app.services.menu_service import MenuService
from app.services.user_service import UserService
from app.services.work_log_service import WorkLogService
from app.services.table_booking_service import TableBookingService
from app.services.analytics_service import AnalyticsService
from app.schemas.schemas import OrderItemCreate, MenuItemCreate
from app.models.user import User
from app.models.order import Order
from app.models.menu import MenuItem
from app.models.table import RestaurantTable
from app.models.work_log import WorkLog
from app.models.table_booking import TableBooking
from app.utils.form_parsers import parse_order_items


# ---------- Auth Service ----------
class TestAuthService:
    def test_register_success(self, db_session):
        user = AuthService.register(db_session, "newuser", "pass123")
        assert user.username == "newuser"
        assert user.role == "waiter"
        assert user.id is not None

    def test_register_duplicate_username(self, db_session, test_user_waiter):
        with pytest.raises(HTTPException) as exc:
            AuthService.register(db_session, test_user_waiter.username, "pass")
        assert exc.value.status_code == 400
        assert "Username already taken" in exc.value.detail

    def test_login_success(self, db_session, test_user_waiter):
        token = AuthService.login(db_session, test_user_waiter.username, "pass123")
        assert isinstance(token, str) and len(token) > 10

    def test_login_wrong_password(self, db_session, test_user_waiter):
        with pytest.raises(HTTPException) as exc:
            AuthService.login(db_session, test_user_waiter.username, "wrong")
        assert exc.value.status_code == 401

    def test_login_user_not_exists(self, db_session):
        with pytest.raises(HTTPException) as exc:
            AuthService.login(db_session, "nonexistent", "pass")
        assert exc.value.status_code == 401


# ---------- Menu Service ----------
class TestMenuService:
    def test_create_menu_item(self, db_session):
        item = MenuService.create(db_session, "Burger", 8.99, "Fast Food", "meat, bun", "Grill", 15)
        assert item.name == "Burger" and item.price == 8.99

    def test_get_all_empty(self, db_session):
        assert MenuService.get_all(db_session) == []

    def test_get_all_with_items(self, db_session, test_menu_item):
        items = MenuService.get_all(db_session)
        assert len(items) == 1 and items[0].name == "Pizza"

    def test_get_by_id_not_found(self, db_session):
        with pytest.raises(HTTPException) as exc:
            MenuService.get_by_id(db_session, 999)
        assert exc.value.status_code == 404

    def test_update_menu_item(self, db_session, test_menu_item):
        updated = MenuService.update(db_session, test_menu_item.id, "New Pizza", 15.0, "Main", "cheese", "bake", 25)
        assert updated.name == "New Pizza" and updated.price == 15.0

    def test_delete_menu_item(self, db_session, test_menu_item):
        MenuService.delete(db_session, test_menu_item.id)
        with pytest.raises(HTTPException):
            MenuService.get_by_id(db_session, test_menu_item.id)


# ---------- Table Service ----------
class TestTableService:
    def test_create_table(self, db_session):
        table = TableService.create(db_session, 10, 6)
        assert table.number == 10 and table.seats == 6 and not table.occupied

    def test_create_table_duplicate_number(self, db_session, test_table):
        with pytest.raises(HTTPException) as exc:
            TableService.create(db_session, test_table.number, 4)
        assert exc.value.status_code == 400

    def test_get_all_tables(self, db_session, test_table):
        tables = TableService.get_all(db_session)
        assert len(tables) == 1 and tables[0].number == test_table.number

    def test_occupy_table(self, db_session, test_table):
        table = TableService.occupy(db_session, test_table.id)
        assert table.occupied is True

    def test_occupy_already_occupied(self, db_session, test_table_occupied):
        with pytest.raises(HTTPException):
            TableService.occupy(db_session, test_table_occupied.id)

    def test_free_table(self, db_session, test_table_occupied):
        table = TableService.free(db_session, test_table_occupied.id)
        assert table.occupied is False

    def test_delete_table_success(self, db_session, test_table):
        TableService.delete(db_session, test_table.id)
        assert TableService.get_by_id(db_session, test_table.id) is None

    def test_delete_table_with_active_orders(self, db_session, test_table, test_order):
        with pytest.raises(HTTPException) as exc:
            TableService.delete(db_session, test_table.id)
        assert exc.value.status_code == 400


# ---------- Order Service ----------
class TestOrderService:
    def test_create_order_success(self, db_session, test_user_waiter, test_table, test_menu_item):
        items = [OrderItemCreate(menu_item_id=test_menu_item.id, quantity=2)]
        order = OrderService.create(db_session, test_user_waiter.id, test_table.id, items, "Test")
        assert order.status == "new" and order.total_amount == test_menu_item.price * 2
        assert TableService.get_by_id(db_session, test_table.id).occupied is True

    def test_create_order_table_not_found(self, db_session, test_user_waiter, test_menu_item):
        items = [OrderItemCreate(menu_item_id=test_menu_item.id, quantity=1)]
        with pytest.raises(HTTPException) as exc:
            OrderService.create(db_session, test_user_waiter.id, 999, items)
        assert exc.value.status_code == 404

    def test_create_order_table_already_occupied(self, db_session, test_user_waiter, test_table_occupied, test_menu_item):
        items = [OrderItemCreate(menu_item_id=test_menu_item.id, quantity=1)]
        with pytest.raises(HTTPException) as exc:
            OrderService.create(db_session, test_user_waiter.id, test_table_occupied.id, items)
        assert exc.value.status_code == 400

    def test_create_order_empty_items(self, db_session, test_user_waiter, test_table):
        with pytest.raises(HTTPException) as exc:
            OrderService.create(db_session, test_user_waiter.id, test_table.id, [])
        assert exc.value.status_code == 400

    def test_change_status_valid(self, db_session, test_order):
        updated = OrderService.change_status(db_session, test_order.id, "cooking")
        assert updated.status == "cooking"

    def test_change_status_to_paid_releases_table(self, db_session, test_order, test_table):
        assert TableService.get_by_id(db_session, test_table.id).occupied is True
        OrderService.change_status(db_session, test_order.id, "paid")
        assert TableService.get_by_id(db_session, test_table.id).occupied is False
        assert OrderService.get_by_id(db_session, test_order.id).status == "paid"

    def test_change_status_invalid(self, db_session, test_order):
        with pytest.raises(HTTPException) as exc:
            OrderService.change_status(db_session, test_order.id, "invalid")
        assert exc.value.status_code == 400

    def test_change_status_from_paid_forbidden(self, db_session, test_order):
        OrderService.change_status(db_session, test_order.id, "paid")
        with pytest.raises(HTTPException) as exc:
            OrderService.change_status(db_session, test_order.id, "new")
        assert exc.value.status_code == 400

    def test_delete_order_releases_table(self, db_session, test_order, test_table):
        assert TableService.get_by_id(db_session, test_table.id).occupied is True
        OrderService.delete(db_session, test_order.id)
        assert TableService.get_by_id(db_session, test_table.id).occupied is False

    def test_get_orders_with_items_exclude_paid(self, db_session, test_user_waiter, test_order, test_table, test_menu_item):
        # Создаём новый стол
        table2 = RestaurantTable(number=99, seats=2, occupied=False)
        db_session.add(table2)
        db_session.commit()
    
        items = [OrderItemCreate(menu_item_id=test_menu_item.id, quantity=1)]
        order2 = OrderService.create(db_session, test_user_waiter.id, table2.id, items)
        OrderService.change_status(db_session, order2.id, "paid")
        orders = OrderService.get_orders_with_items(db_session, user_id=test_user_waiter.id, exclude_statuses=["paid"])
        assert len(orders) == 1 and orders[0].id == test_order.id

    def test_get_allowed_statuses_for_role(self):
        assert OrderService.get_allowed_statuses_for_role("admin") == ["new", "cooking", "ready", "paid"]
        assert OrderService.get_allowed_statuses_for_role("cook") == ["cooking", "ready"]
        assert OrderService.get_allowed_statuses_for_role("waiter") == ["new", "paid"]


# ---------- User Service ----------
class TestUserService:
    def test_get_all_users(self, db_session, test_user_waiter, test_user_cook, test_user_admin):
        users = UserService.get_all(db_session)
        assert len(users) >= 3

    def test_change_role_valid(self, db_session, test_user_waiter):
        updated = UserService.change_role(db_session, test_user_waiter.id, "admin")
        assert updated.role == "admin"

    def test_change_role_invalid(self, db_session, test_user_waiter):
        with pytest.raises(HTTPException) as exc:
            UserService.change_role(db_session, test_user_waiter.id, "invalid")
        assert exc.value.status_code == 400

    def test_update_hourly_rate(self, db_session, test_user_waiter):
        UserService.update_hourly_rate(db_session, test_user_waiter.id, 350)
        user = db_session.query(User).filter(User.id == test_user_waiter.id).first()
        assert user.hourly_rate == 350

    def test_delete_user_cascade(self, db_session, test_user_waiter, test_order, test_booking, test_work_log):
        # Сохраняем ID до удаления
        user_id = test_user_waiter.id
        order_id = test_order.id
        booking_id = test_booking.id
        work_log_id = test_work_log.id
    
        # Выполняем удаление
        UserService.delete_user(db_session, user_id)
    
        # Очищаем сессию, чтобы гарантировать новые запросы
        db_session.expunge_all()
    
        # Проверяем через свежие запросы
        assert db_session.query(User).filter(User.id == user_id).first() is None
        assert db_session.query(Order).filter(Order.id == order_id).first() is None
        assert db_session.query(TableBooking).filter(TableBooking.id == booking_id).first() is None
        assert db_session.query(WorkLog).filter(WorkLog.id == work_log_id).first() is None


# ---------- WorkLog Service ----------
class TestWorkLogService:
    def test_add_hours(self, db_session, test_user_waiter):
        log = WorkLogService.add_hours(db_session, test_user_waiter.id, 8.0)
        assert log.hours == 8.0

    def test_get_user_hours(self, db_session, test_user_waiter, test_work_log):
        total = WorkLogService.get_user_hours(db_session, test_user_waiter.id)
        assert total == test_work_log.hours

    def test_get_user_salary(self, db_session, test_user_waiter, test_work_log):
        salary = WorkLogService.get_user_salary(db_session, test_user_waiter.id, 200)
        assert salary == test_work_log.hours * 200


# ---------- TableBooking Service ----------
class TestTableBookingService:
    def test_create_booking_success(self, db_session, test_user_waiter, test_table):
        future_time = datetime.utcnow() + timedelta(days=2, hours=18)
        booking = TableBookingService.create_booking(db_session, test_user_waiter.id, test_table.id, future_time)
        assert booking.status == "active"

    def test_create_booking_past_time(self, db_session, test_user_waiter, test_table):
        past_time = datetime.utcnow() - timedelta(hours=1)
        with pytest.raises(HTTPException) as exc:
            TableBookingService.create_booking(db_session, test_user_waiter.id, test_table.id, past_time)
        assert exc.value.status_code == 400

    def test_create_booking_table_already_booked(self, db_session, test_user_waiter, test_table, test_booking):
        db_session.expire_all()
        same_time = test_booking.booking_time
        with pytest.raises(HTTPException) as exc:
            TableBookingService.create_booking(db_session, test_user_waiter.id, test_table.id, same_time)
        assert exc.value.status_code == 400

    def test_get_week_bookings(self, db_session, test_booking):
        bookings = TableBookingService.get_week_bookings(db_session)
        assert len(bookings) >= 1

    def test_cancel_booking_by_owner(self, db_session, test_booking, test_user_waiter):
        cancelled = TableBookingService.cancel_booking(db_session, test_booking.id, test_user_waiter.id, is_admin=False)
        assert cancelled.status == "cancelled"

    def test_cancel_booking_by_other_forbidden(self, db_session, test_booking, test_user_cook):
        with pytest.raises(HTTPException) as exc:
            TableBookingService.cancel_booking(db_session, test_booking.id, test_user_cook.id, is_admin=False)
        assert exc.value.status_code == 403


# ---------- Analytics Service ----------
class TestAnalyticsService:
    @patch("app.services.analytics_service.date")
    def test_get_dashboard(self, mock_date, db_session, test_order, test_table, test_menu_item):
        from datetime import date as real_date
        mock_date.today.return_value = real_date.today()
    
        # Создаём новый стол
        new_table = RestaurantTable(number=100, seats=2, occupied=False)
        db_session.add(new_table)
        db_session.commit()
    
        items = [OrderItemCreate(menu_item_id=test_menu_item.id, quantity=1)]
        order = OrderService.create(db_session, test_order.user_id, new_table.id, items)
        OrderService.change_status(db_session, order.id, "paid")
        data = AnalyticsService.get_dashboard(db_session)
        assert "revenue" in data

    def test_get_dashboard_empty(self, db_session):
        data = AnalyticsService.get_dashboard(db_session)
        assert data["revenue"] == 0.0
        assert data["status_stats"] == []
        assert data["top_dishes"] == []
        assert data["table_load"] == "0/0"


# ---------- Form Parsers ----------
class TestFormParsers:
    def test_parse_order_items(self):
        form_data = {
            "item_1": "1",
            "quantity_1": "3",
            "item_2": "1",
            "quantity_2": "1",
            "other_field": "value"
        }
        from fastapi.datastructures import FormData
        form = FormData(form_data)
        items = parse_order_items(form)
        assert len(items) == 2
        assert items[0].menu_item_id == 1 and items[0].quantity == 3
        assert items[1].menu_item_id == 2 and items[1].quantity == 1

    def test_parse_order_items_empty(self):
        form_data = {}
        from fastapi.datastructures import FormData
        form = FormData(form_data)
        items = parse_order_items(form)
        assert items == []


# ---------- Edge Cases ----------
class TestEdgeCases:
    def test_menu_item_negative_price_validation(self):
        with pytest.raises(ValidationError):
            MenuItemCreate(name="Bad", price=-10, category="test")

    def test_order_item_zero_quantity_validation(self):
        from app.schemas.schemas import OrderItemCreate
        with pytest.raises(ValidationError):
            OrderItemCreate(menu_item_id=1, quantity=0)

    def test_booking_overlapping_boundary(self, db_session, test_user_waiter, test_table, test_booking):
        db_session.expire_all()
        same_time = test_booking.booking_time
        with pytest.raises(HTTPException):
            TableBookingService.create_booking(db_session, test_user_waiter.id, test_table.id, same_time)


# ==================== Дополнительные тесты для повышения покрытия ====================
class TestAdditionalCoverage:
    
    def test_get_expired_bookings_empty(self, db_session):
        """Проверяем, что метод get_expired_bookings работает (пустой список)"""
        bookings = TableBookingService.get_expired_bookings(db_session)
        assert bookings == []

    def test_get_week_bookings_with_custom_start_date(self, db_session, test_booking):
        """Проверяем ветку с переданным start_date в get_week_bookings"""
        from datetime import datetime, timedelta
        start_date = datetime.utcnow() - timedelta(days=1)
        bookings = TableBookingService.get_week_bookings(db_session, start_date=start_date)
        # Просто проверяем, что метод не падает
        assert isinstance(bookings, list)

    def test_order_service_grouped_by_date_with_limit(self, db_session, test_order):
        """Проверяем параметр limit_days в get_orders_grouped_by_date"""
        stats = OrderService.get_orders_grouped_by_date(db_session, user_id=None, limit_days=1)
        assert isinstance(stats, list)

    def test_user_service_update_hourly_rate_not_found(self, db_session):
        """Проверяем обработку несуществующего пользователя"""
        with pytest.raises(HTTPException) as exc:
            UserService.update_hourly_rate(db_session, 9999, 100)
        assert exc.value.status_code == 404

    def test_order_service_create_invalid_menu_item(self, db_session, test_user_waiter, test_table):
        """Создание заказа с несуществующим блюдом -> 404"""
        from app.schemas.schemas import OrderItemCreate
        items = [OrderItemCreate(menu_item_id=9999, quantity=1)]
        with pytest.raises(HTTPException) as exc:
            OrderService.create(db_session, test_user_waiter.id, test_table.id, items)
        assert exc.value.status_code == 404

    def test_menu_service_update_not_found(self, db_session):
        """Обновление несуществующего блюда -> 404"""
        with pytest.raises(HTTPException) as exc:
            MenuService.update(db_session, 9999, "Test", 10.0, "Cat")
        assert exc.value.status_code == 404

    def test_table_service_occupy_not_found(self, db_session):
        """Занятие несуществующего стола -> 404"""
        with pytest.raises(HTTPException) as exc:
            TableService.occupy(db_session, 9999)
        assert exc.value.status_code == 404

    def test_table_service_free_not_found(self, db_session):
        """Освобождение несуществующего стола -> 404"""
        with pytest.raises(HTTPException) as exc:
            TableService.free(db_session, 9999)
        assert exc.value.status_code == 404

    def test_order_service_delete_not_found(self, db_session):
        """Удаление несуществующего заказа -> 404"""
        with pytest.raises(HTTPException) as exc:
            OrderService.delete(db_session, 9999)
        assert exc.value.status_code == 404

    def test_table_booking_cancel_not_found(self, db_session, test_user_waiter):
        """Отмена несуществующей брони -> 404"""
        with pytest.raises(HTTPException) as exc:
            TableBookingService.cancel_booking(db_session, 9999, test_user_waiter.id, is_admin=False)
        assert exc.value.status_code == 404

    def test_security_hash_long_password(self):
        """Покрываем обрезание пароля до 72 байт (security.py)"""
        from app.core.security import hash_password, verify_password
        long_pass = "a" * 100
        hashed = hash_password(long_pass)
        assert verify_password(long_pass, hashed)

    def test_config_settings_extra_ignore(self):
        """Покрываем настройки config.py (ветка extra='ignore')"""
        from app.core.config import settings
        assert hasattr(settings, "SECRET_KEY")