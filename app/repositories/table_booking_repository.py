from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.table_booking import TableBooking

class TableBookingRepository:
    @staticmethod
    def get_by_id(db: Session, booking_id: int) -> TableBooking | None:
        return db.query(TableBooking).filter(TableBooking.id == booking_id).first()

    @staticmethod
    def get_active_by_table(db: Session, table_id: int, from_time: datetime = None):
        if from_time is None:
            from_time = datetime.utcnow()
        return db.query(TableBooking).filter(
            TableBooking.table_id == table_id,
            TableBooking.status == "active",
            TableBooking.booking_time >= from_time
        ).order_by(TableBooking.booking_time).all()

    @staticmethod
    def is_table_booked(db: Session, table_id: int, check_time: datetime) -> bool:
        """Проверяет, забронирован ли стол на указанное время (длительность 2 часа по умолчанию)"""
        # Для простоты считаем, что бронь длится 2 часа (120 минут)
        end_time = check_time + timedelta(minutes=120)
        overlapping = db.query(TableBooking).filter(
            TableBooking.table_id == table_id,
            TableBooking.status == "active",
            TableBooking.booking_time < end_time,
            TableBooking.booking_time + timedelta(minutes=120) > check_time
        ).first()
        return overlapping is not None

    @staticmethod
    def create(db: Session, table_id: int, user_id: int, booking_time: datetime) -> TableBooking:
        booking = TableBooking(
            table_id=table_id,
            user_id=user_id,
            booking_time=booking_time
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)
        return booking

    @staticmethod
    def cancel(db: Session, booking: TableBooking) -> TableBooking:
        booking.status = "cancelled"
        db.commit()
        db.refresh(booking)
        return booking