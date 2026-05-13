import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.menu import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.repositories.order_repository import OrderRepository
from app.schemas.schemas import OrderItemCreate

logger = logging.getLogger(__name__)

VALID_STATUSES = {"new", "cooking", "ready", "paid"}


class OrderService:

    @staticmethod
    def create(db: Session, user_id: int, table_id: int, items: list[OrderItemCreate], notes: str | None = None) -> Order:
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
        db.commit()
        db.refresh(order)
        logger.info("Order %d created for user %d", order.id, user_id)
        return order

    @staticmethod
    def change_status(db: Session, order_id: int, status: str) -> Order:
        if status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Valid: {VALID_STATUSES}")
        order = OrderRepository.get_by_id(db, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return OrderRepository.update_status(db, order, status)

    @staticmethod
    def delete(db: Session, order_id: int) -> dict:
        order = OrderRepository.get_by_id(db, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        OrderRepository.delete(db, order)
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