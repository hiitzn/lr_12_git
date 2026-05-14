from sqlalchemy.orm import Session
from app.models.work_log import WorkLog
from datetime import datetime
class WorkLogRepository:
    @staticmethod
    def get_by_user(db: Session, user_id: int):
        return db.query(WorkLog).filter(WorkLog.user_id == user_id).all()

    @staticmethod
    def create(db: Session, user_id: int, hours: float, date: datetime = None):
        if date is None:
            date = datetime.utcnow()
        log = WorkLog(user_id=user_id, hours=hours, date=date)
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def delete(db: Session, log_id: int):
        log = db.query(WorkLog).filter(WorkLog.id == log_id).first()
        if log:
            db.delete(log)
            db.commit()