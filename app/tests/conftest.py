import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Устанавливаем флаг тестирования для отключения жесткого лимитера
os.environ["TESTING"] = "true"

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.core.config import settings
from app.main import app
from app.models.user import User
from app.models.table import RestaurantTable
from app.models.menu import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.table_booking import TableBooking
from app.models.work_log import WorkLog

# ---------- Настройки для тестов ----------
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ADMIN_PASSWORD"] = "admin123"
settings.SECRET_KEY = "test-secret-key"
settings.ADMIN_PASSWORD = "admin123"
settings.COOKIE_SECURE = False
settings.BOOKING_DURATION_MINUTES = 120

# ---------- In-memory БД ----------
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

# ---------- Фикстуры БД и клиента ----------
@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    def _get_db_override():
        return db_session
    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(db_session):
    def _get_db_override():
        return db_session
    app.dependency_overrides[get_db] = _get_db_override
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------- Мок datetime (фиксированное время UTC) ----------
@pytest.fixture(autouse=True)
def mock_datetime(monkeypatch):
    class FixedDatetime(datetime):
        @classmethod
        def utcnow(cls):
            return datetime(2025, 1, 1, 12, 0, 0)
        @classmethod
        def now(cls, tz=None):
            return datetime(2025, 1, 1, 12, 0, 0)
    monkeypatch.setattr("datetime.datetime", FixedDatetime)
    return FixedDatetime


# ---------- Мок настроек (autouse) ----------
@pytest.fixture(autouse=True)
def mock_settings():
    with patch.object(settings, "COOKIE_SECURE", False), \
         patch.object(settings, "SECRET_KEY", "test-secret-key"):
        yield


# ---------- Тестовые данные ----------
@pytest.fixture(scope="function")
def test_user_waiter(db_session):
    user = User(username="waiter1", password=hash_password("pass123"), role="waiter", hourly_rate=200)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_user_cook(db_session):
    user = User(username="cook1", password=hash_password("pass123"), role="cook", hourly_rate=250)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_user_admin(db_session):
    user = User(username="admin1", password=hash_password("admin123"), role="admin", hourly_rate=300)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_table(db_session):
    table = RestaurantTable(number=1, seats=4, occupied=False)
    db_session.add(table)
    db_session.commit()
    db_session.refresh(table)
    return table


@pytest.fixture(scope="function")
def test_table_occupied(db_session):
    table = RestaurantTable(number=2, seats=2, occupied=True)
    db_session.add(table)
    db_session.commit()
    db_session.refresh(table)
    return table


@pytest.fixture(scope="function")
def test_menu_item(db_session):
    item = MenuItem(
        name="Pizza",
        price=12.5,
        category="Main",
        ingredients="dough, cheese, tomato",
        instructions="Bake at 200C",
        cooking_time=20
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


@pytest.fixture(scope="function")
def test_order(db_session, test_user_waiter, test_table, test_menu_item):
    order = Order(
        user_id=test_user_waiter.id,
        table_id=test_table.id,
        status="new",
        total_amount=12.5,
        notes="test"
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)

    order_item = OrderItem(order_id=order.id, menu_item_id=test_menu_item.id, quantity=2)
    db_session.add(order_item)
    db_session.commit()

    test_table.occupied = True
    db_session.commit()
    return order


@pytest.fixture(scope="function")
def test_booking(db_session, test_user_waiter, test_table):
    booking_time = datetime.utcnow() + timedelta(days=1, hours=18)
    booking = TableBooking(
        table_id=test_table.id,
        user_id=test_user_waiter.id,
        booking_time=booking_time,
        status="active"
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)
    return booking


@pytest.fixture(scope="function")
def test_work_log(db_session, test_user_waiter):
    log = WorkLog(user_id=test_user_waiter.id, hours=5.5, created_at=datetime.utcnow())
    db_session.add(log)
    db_session.commit()
    db_session.refresh(log)
    return log