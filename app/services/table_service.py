import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.table import RestaurantTable
from app.repositories.table_repository import TableRepository

logger = logging.getLogger(__name__)


class TableService:

    @staticmethod
    def get_all(db: Session) -> list[RestaurantTable]:
        return TableRepository.get_all(db)

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
        table = TableService._get_or_404(db, table_id)
        TableRepository.delete(db, table)