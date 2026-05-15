import logging
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.user_repository import UserRepository
from sqlalchemy import func
from app.models.work_log import WorkLog
from app.models.table_booking import TableBooking
from app.services.order_service import OrderService

logger = logging.getLogger(__name__)
VALID_ROLES = {"waiter", "cook", "admin"}


class UserService:

    @staticmethod
    def get_all(db: Session) -> list[User]:
        return UserRepository.get_all(db)

    @staticmethod
    def update_hourly_rate(db: Session, user_id: int, new_rate: int):
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(404, "Пользователь не найден")
        user.hourly_rate = new_rate
        db.commit()

    @staticmethod
    def change_role(db: Session, user_id: int, role: str) -> User:
        if role not in VALID_ROLES:
            raise HTTPException(400, f"Invalid role. Valid: {VALID_ROLES}")
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(404, "User not found")
        updated = UserRepository.update_role(db, user, role)
        logger.info("User %d role changed to %s", user_id, role)
        return updated

    @staticmethod
    def delete_user(db: Session, user_id: int) -> None:
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(404, "User not found")
    
        # Удаляем связанные записи
        db.query(WorkLog).filter(WorkLog.user_id == user_id).delete()
        db.query(TableBooking).filter(TableBooking.user_id == user_id).delete()
    
        # Собираем ID заказов и удаляем их (освобождая столы)
        order_ids = [order.id for order in user.orders]
        for oid in order_ids:
            OrderService.delete(db, oid)
    
        UserRepository.delete(db, user)
        db.commit()

    @staticmethod
    def get_users_with_salary_stats(db: Session) -> list[dict]:
        result = db.query(
            User.username,
            User.role,
            User.hourly_rate,
            func.coalesce(func.sum(WorkLog.hours), 0).label('total_hours')
        ).outerjoin(WorkLog, User.id == WorkLog.user_id).group_by(User.id).all()

        stats = []
        for username, role, hourly_rate, total_hours in result:
            salary = total_hours * hourly_rate
            stats.append({
                "username": username,
                "role": role,
                "hourly_rate": hourly_rate,
                "total_hours": total_hours,
                "salary": salary
            })
        return stats