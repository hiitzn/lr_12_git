import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.menu import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.repositories.order_repository import OrderRepository
from app.repositories.table_repository import TableRepository
from app.services.table_service import TableService
from app.schemas.schemas import OrderItemCreate

logger = logging.getLogger(__name__)

VALID_STATUSES = {"new", "cooking", "ready", "paid"}


class OrderService:

    @staticmethod
    def create(db: Session, user_id: int, table_id: int, items: list[OrderItemCreate], notes: str | None = None) -> Order:
        # Проверка существования стола и его занятости
        table = TableService.get_by_id(db, table_id)
        if not table:
            raise HTTPException(status_code=404, detail="Table not found")
        if table.occupied:
            raise HTTPException(status_code=400, detail="Стол уже занят. Освободите или выберите другой.")

        order = Order(user_id=user_id, table_id=table_id, status="new", notes=notes)
        db.add(order)
        db.flush()

        total = 0.0
        for item in items:
            menu_item = db.query(MenuItem).filter(MenuItem.id == item.menu_item_id).first()
            if not menu_item:
                db.rollback()
                raise HTTPException(
                    status_code=404,
                    detail=f"Menu item {item.menu_item_id} not found",
                )
            total += menu_item.price * item.quantity
            db.add(OrderItem(order_id=order.id, menu_item_id=menu_item.id, quantity=item.quantity))

        order.total_amount = total
        # Автоматически занимаем стол
        TableRepository.set_occupied(db, table, True)
        db.commit()
        db.refresh(order)
        logger.info("Order %d created for user %d, table %d occupied", order.id, user_id, table_id)
        return order

    @staticmethod
    def change_status(db: Session, order_id: int, status: str) -> Order:
        if status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Valid: {VALID_STATUSES}")
        order = OrderRepository.get_by_id(db, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Если статус меняется на "paid" – освобождаем стол
        if status == "paid" and order.status != "paid":
            table = TableService.get_by_id(db, order.table_id)
            if table and table.occupied:
                TableRepository.set_occupied(db, table, False)
                logger.info("Table %d freed after order %d paid", order.table_id, order_id)

        return OrderRepository.update_status(db, order, status)

    @staticmethod
    def delete(db: Session, order_id: int) -> dict:
        order = OrderRepository.get_by_id(db, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Освобождаем стол, если он был занят
        table = TableService.get_by_id(db, order.table_id)
        if table and table.occupied:
            TableRepository.set_occupied(db, table, False)
            logger.info("Table %d freed after order %d deleted", order.table_id, order_id)

        OrderRepository.delete(db, order)
        logger.info("Order %d deleted", order_id)
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