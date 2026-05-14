from sqlalchemy.orm import Session
from app.repositories.work_log_repository import WorkLogRepository
from datetime import datetime

class WorkLogService:
    @staticmethod
    def add_hours(db: Session, user_id: int, hours: float, date: datetime = None):
        return WorkLogRepository.create(db, user_id, hours, date)

    @staticmethod
    def get_user_hours(db: Session, user_id: int) -> float:
        logs = WorkLogRepository.get_by_user(db, user_id)
        return sum(log.hours for log in logs)

    @staticmethod
    def get_user_salary(db: Session, user_id: int, hourly_rate: int) -> float:
        total_hours = WorkLogService.get_user_hours(db, user_id)
        return total_hours * hourly_rate