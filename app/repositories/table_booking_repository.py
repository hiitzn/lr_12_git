from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.table_booking import TableBooking
from app.core.config import settings


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
        duration = timedelta(minutes=settings.BOOKING_DURATION_MINUTES)
        check_end = check_time + duration

        # Ищем любую активную бронь, которая пересекается с [check_time, check_end]
        # SQLite не умеет сложение datetime + timedelta, поэтому используем Python
        all_bookings = db.query(TableBooking).filter(
            TableBooking.table_id == table_id,
            TableBooking.status == "active"
        ).all()
        for booking in all_bookings:
            booking_end = booking.booking_time + duration
            if booking.booking_time < check_end and booking_end > check_time:
                return True
        return False

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