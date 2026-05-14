from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from app.core.database import Base

class TableBooking(Base):
    __tablename__ = "table_bookings"

    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    booking_time = Column(DateTime, nullable=False)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    table = relationship("RestaurantTable", back_populates="bookings")
    user = relationship("User")