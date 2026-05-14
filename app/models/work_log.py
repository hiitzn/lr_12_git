from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

class WorkLog(Base):
    __tablename__ = "work_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    hours = Column(Float, nullable=False)  # количество отработанных часов
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    user = relationship("User", backref="work_logs")