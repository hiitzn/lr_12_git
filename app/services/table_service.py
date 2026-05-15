import logging
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from app.models.order import Order
from app.models.table import RestaurantTable
from app.repositories.table_repository import TableRepository

logger = logging.getLogger(__name__)


class TableService:

    @staticmethod
    def get_all(db: Session) -> list[RestaurantTable]:
        return TableRepository.get_all(db)

    @staticmethod
    def get_all_with_bookings(db: Session) -> list[RestaurantTable]:
        from sqlalchemy.orm import joinedload
        now = datetime.utcnow()  # naive UTC
        tables = db.query(RestaurantTable).options(
            joinedload(RestaurantTable.bookings)
        ).all()
        for table in tables:
            if table.bookings:
                table.bookings = [b for b in table.bookings if b.status == "active" and b.booking_time >= now]
        return tables

    @staticmethod
    def create(db: Session, number: int, seats: int) -> RestaurantTable:
        if TableRepository.get_by_number(db, number):
            raise HTTPException(status_code=400, detail="Table with this number already exists")
        return TableRepository.create(db, number, seats)

    @staticmethod
    def _get_or_404(db: Session, table_id: int) -> RestaurantTable:
        table = TableRepository.get_by_id(db, table_id)
        if not table:
            raise HTTPException(status_code=404, detail="Table not found")
        return table

    @staticmethod
    def occupy(db: Session, table_id: int) -> RestaurantTable:
        table = TableService._get_or_404(db, table_id)
        return TableRepository.set_occupied(db, table, True)

    @staticmethod
    def free(db: Session, table_id: int) -> RestaurantTable:
        table = TableService._get_or_404(db, table_id)
        return TableRepository.set_occupied(db, table, False)

    @staticmethod
    def delete(db: Session, table_id: int) -> None:
        # Проверяем, есть ли активные заказы за этим столом
        active_order = db.query(Order).filter(
            Order.table_id == table_id,
            Order.status != "paid"
        ).first()
        if active_order:
            raise HTTPException(status_code=400, detail="Нельзя удалить стол с активными заказами")
    
        table = TableService._get_or_404(db, table_id)
        TableRepository.delete(db, table)

    @staticmethod
    def get_by_id(db: Session, table_id: int) -> RestaurantTable | None:
        return TableRepository.get_by_id(db, table_id)