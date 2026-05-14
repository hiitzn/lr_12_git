from sqlalchemy import Column, Float, Integer, String, Text
from app.core.database import Base

class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    # Поля для рецепта
    ingredients = Column(Text, nullable=True)   # ингредиенты
    instructions = Column(Text, nullable=True)  # инструкция приготовления
    cooking_time = Column(Integer, default=30)  # время приготовления