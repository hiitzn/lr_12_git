import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.menu import MenuItem
from sqlalchemy import update
from app.models.table import RestaurantTable
from app.models.order import Order
from app.models.order_item import OrderItem
from app.repositories.order_repository import OrderRepository
from app.repositories.table_repository import TableRepository
from app.services.table_service import TableService
from app.schemas.schemas import OrderItemCreate
from datetime import datetime, timezone
from app.repositories.table_booking_repository import TableBookingRepository
from app.core.config import settings

logger = logging.getLogger(__name__)

VALID_STATUSES = {"new", "cooking", "ready", "paid"}


class OrderService:

    @staticmethod
    def create(db: Session, user_id: int, table_id: int, items: list[OrderItemCreate], notes: str | None = None) -> Order:
        # 1. Проверка: заказ не может быть пустым
        if not items:
            raise HTTPException(400, "Заказ должен содержать хотя бы одно блюдо")

        # 2. Проверка существования стола
        table = db.query(RestaurantTable).filter(RestaurantTable.id == table_id).first()
        if not table:
            raise HTTPException(404, "Table not found")

        # 3. Проверка брони на текущее время (используем UTC)
        now = datetime.utcnow()
        if TableBookingRepository.is_table_booked(db, table_id, now):
            raise HTTPException(400, "Стол уже забронирован на это время")

        # 4. Атомарно занимаем стол (только если свободен)
        result = db.execute(
            update(RestaurantTable)
            .where(RestaurantTable.id == table_id, RestaurantTable.occupied == False)
            .values(occupied=True)
        )
        if result.rowcount == 0:
            raise HTTPException(400, "Стол уже занят")

        # 5. Создаём заказ
        order = Order(user_id=user_id, table_id=table_id, status="new", notes=notes)
        db.add(order)
        db.flush()   # получаем order.id

        # 6. Добавляем позиции и считаем сумму
        total = 0.0
        for item in items:
            menu_item = db.query(MenuItem).filter(MenuItem.id == item.menu_item_id).first()
            if not menu_item:
                raise HTTPException(404, f"Menu item {item.menu_item_id} not found")
            total += menu_item.price * item.quantity
            db.add(OrderItem(order_id=order.id, menu_item_id=menu_item.id, quantity=item.quantity))

        order.total_amount = total
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def change_status(db: Session, order_id: int, status: str) -> Order:
        if status not in VALID_STATUSES:
            raise HTTPException(400, f"Invalid status. Valid: {VALID_STATUSES}")
        order = OrderRepository.get_by_id(db, order_id)
        if not order:
            raise HTTPException(404, "Order not found")

        # Запрещаем переход из paid в любой другой статус
        if order.status == "paid" and status != "paid":
            raise HTTPException(400, "Нельзя изменить статус оплаченного заказа")

        # Если статус меняется на "paid" – освобождаем стол (и только тогда)
        if status == "paid" and order.status != "paid":
            table = TableService.get_by_id(db, order.table_id)
            if table and table.occupied:
                table.occupied = False   # освобождаем стол без отдельного коммита

        order.status = status
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def delete(db: Session, order_id: int) -> dict:
        order = OrderRepository.get_by_id(db, order_id)
        if not order:
            raise HTTPException(404, "Order not found")

        table = TableService.get_by_id(db, order.table_id)
        if table and table.occupied:
            table.occupied = False

        db.delete(order)   # удаляем заказ
        return {"message": "Order deleted"}

    @staticmethod
    def get_orders_for_user(db: Session, user_id: int) -> list[Order]:
        return db.query(Order).filter(Order.user_id == user_id).all()

    @staticmethod
    def get_kitchen_orders(db: Session):
        return db.query(Order).filter(Order.status.in_(["new", "cooking", "ready"])).all()

    @staticmethod
    def get_all_orders(db: Session) -> list[Order]:
        return OrderRepository.get_all(db)

    @staticmethod
    def get_by_id(db: Session, order_id: int) -> Order:
        order = OrderRepository.get_by_id(db, order_id)
        if not order:
            raise HTTPException(404, "Order not found")
        return order

    # ---------- Методы для устранения DRY (используются в pages.py) ----------
    @staticmethod
    def get_orders_with_items(db: Session, user_id: int | None = None, exclude_statuses: list[str] | None = None) -> list[Order]:
        from sqlalchemy.orm import joinedload
        query = db.query(Order).options(
            joinedload(Order.items).joinedload(OrderItem.menu_item),
            joinedload(Order.user),
            joinedload(Order.table)
        )
        if user_id is not None:
            query = query.filter(Order.user_id == user_id)
        if exclude_statuses:
            query = query.filter(Order.status.notin_(exclude_statuses))
        return query.all()


    @staticmethod
    def get_allowed_statuses_for_role(role: str, current_status: str = None) -> list[str]:
        """Возвращает список статусов, которые может установить пользователь с данной ролью."""
        if role == "admin":
            return ["new", "cooking", "ready", "paid"]
        elif role == "cook":
            # Повар может установить только cooking или ready
            return ["cooking", "ready"]
        elif role == "waiter":
            # Официант – new или paid
            return ["new", "paid"]
        else:
            return []

    @staticmethod
    def get_orders_grouped_by_date(db: Session, user_id: int | None = None, limit_days: int | None = None) -> list[dict]:
        from datetime import datetime, date
        from sqlalchemy.orm import joinedload
        query = db.query(Order).options(
            joinedload(Order.items).joinedload(OrderItem.menu_item),
            joinedload(Order.user),
            joinedload(Order.table) 
        )
        if user_id is not None:
            query = query.filter(Order.user_id == user_id)
        if limit_days:
            start_date = datetime.combine(date.today(), datetime.min.time())
            query = query.filter(Order.created_at >= start_date)
        orders = query.order_by(Order.created_at.desc()).all()

        groups = {}
        for order in orders:
            date_key = order.created_at.strftime('%Y-%m-%d')
            groups.setdefault(date_key, []).append(order)

        result = []
        for date_key, day_orders in groups.items():
            total = sum(o.total_amount for o in day_orders)
            result.append({
                'date': date_key,
                'orders': day_orders,
                'total': total,
                'count': len(day_orders)
            })
        return result

    @staticmethod
    def get_kitchen_orders_with_details(db: Session) -> list[Order]:
        from sqlalchemy.orm import joinedload
        return db.query(Order).options(
            joinedload(Order.items).joinedload(OrderItem.menu_item),
            joinedload(Order.user),
            joinedload(Order.table)
        ).filter(Order.status.in_(["new", "cooking", "ready"])).order_by(Order.created_at).all()