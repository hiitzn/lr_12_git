from sqlalchemy.orm import Session

from app.models.order import Order


class OrderRepository:

    @staticmethod
    def get_all(db: Session) -> list[Order]:
        return db.query(Order).all()

    @staticmethod
    def get_by_id(db: Session, order_id: int) -> Order | None:
        return db.query(Order).filter(Order.id == order_id).first()

    @staticmethod
    def update_status(db: Session, order: Order, status: str) -> Order:
        order.status = status
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def delete(db: Session, order: Order) -> None:
        db.delete(order)