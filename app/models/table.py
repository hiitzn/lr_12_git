from sqlalchemy import Boolean, Column, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base

class RestaurantTable(Base):
    __tablename__ = "tables"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, unique=True, nullable=False)
    seats = Column(Integer, nullable=False)
    occupied = Column(Boolean, default=False)

    bookings = relationship("TableBooking", back_populates="table", cascade="all, delete")
    orders = relationship("Order", back_populates="table")