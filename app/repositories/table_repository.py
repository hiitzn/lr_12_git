from sqlalchemy.orm import Session

from app.models.table import RestaurantTable


class TableRepository:

    @staticmethod
    def get_all(db: Session) -> list[RestaurantTable]:
        return db.query(RestaurantTable).all()

    @staticmethod
    def get_by_id(db: Session, table_id: int) -> RestaurantTable | None:
        return db.query(RestaurantTable).filter(RestaurantTable.id == table_id).first()

    @staticmethod
    def get_by_number(db: Session, number: int) -> RestaurantTable | None:
        return db.query(RestaurantTable).filter(RestaurantTable.number == number).first()

    @staticmethod
    def create(db: Session, number: int, seats: int) -> RestaurantTable:
        table = RestaurantTable(number=number, seats=seats)
        db.add(table)
        db.commit()
        db.refresh(table)
        return table

    @staticmethod
    def set_occupied(db: Session, table: RestaurantTable, occupied: bool) -> RestaurantTable:
        table.occupied = occupied
        db.commit()
        db.refresh(table)
        return table

    @staticmethod
    def delete(db: Session, table: RestaurantTable) -> None:
        db.delete(table)
        db.commit()