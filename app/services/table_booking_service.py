from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.repositories.table_booking_repository import TableBookingRepository
from app.repositories.table_repository import TableRepository
from app.models.table_booking import TableBooking

class TableBookingService:
    @staticmethod
    def create_booking(db: Session, user_id: int, table_id: int, booking_time: datetime):
        table = TableRepository.get_by_id(db, table_id)
        if not table:
            raise HTTPException(404, "Стол не найден")
        
        # booking_time уже naive (из формы), сравниваем с текущим naive UTC
        now = datetime.utcnow()
        if booking_time < now:
            raise HTTPException(400, "Нельзя забронировать на прошедшее время")
        
        if TableBookingRepository.is_table_booked(db, table_id, booking_time):
            raise HTTPException(400, "Стол уже забронирован на это время")
        
        return TableBookingRepository.create(db, table_id, user_id, booking_time)



    @staticmethod
    def get_week_bookings(db: Session, start_date: datetime = None):
        # 1. Помечаем истекшие активные брони как "expired"
        now = datetime.utcnow()
        db.query(TableBooking).filter(
            TableBooking.booking_time < now,
            TableBooking.status == "active"
        ).update({"status": "expired"}, synchronize_session=False)
        db.commit()
    
        # 2. Берём текущий момент для начала выборки
        if start_date is None:
            start_date = now
        end_date = start_date + timedelta(days=7)
    
        # 3. Выбираем только активные брони в будущем
        bookings = db.query(TableBooking).filter(
            TableBooking.status == "active",
            TableBooking.booking_time >= start_date,
            TableBooking.booking_time < end_date
        ).order_by(TableBooking.booking_time).all()
    
        for b in bookings:
            b.table_number = b.table.number if b.table else None
            b.username = b.user.username if b.user else None
        return bookings

    @staticmethod
    def get_expired_bookings(db: Session, user_id: int | None = None):
        query = db.query(TableBooking).filter(
            TableBooking.status == "expired"
        )
        if user_id:
            query = query.filter(TableBooking.user_id == user_id)
        bookings = query.order_by(TableBooking.booking_time.desc()).all()
        for b in bookings:
            b.table_number = b.table.number if b.table else None
            b.username = b.user.username if b.user else None
        return bookings

    @staticmethod
    def cancel_booking(db: Session, booking_id: int, user_id: int, is_admin: bool):
        booking = TableBookingRepository.get_by_id(db, booking_id)
        if not booking:
            raise HTTPException(404, "Бронь не найдена")
        if booking.user_id != user_id and not is_admin:
            raise HTTPException(403, "Только создатель брони или админ может отменить")
        return TableBookingRepository.cancel(db, booking)