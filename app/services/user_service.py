import logging
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.user_repository import UserRepository
from sqlalchemy import func
from app.models.work_log import WorkLog
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
    
        # Вручную удаляем заказы пользователя через OrderService (чтобы освободить столы)
        for order in user.orders:
            OrderService.delete(db, order.id)  # этот метод освобождает стол
    
        # Альтернатива: удалить все заказы одним запросом, но тогда нужно освободить столы
        # Проще пройтись по каждому заказу.
    
        UserRepository.delete(db, user)
        logger.info("User %d deleted with all orders", user_id)

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