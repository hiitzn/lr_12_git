import logging
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.menu import MenuItem
from app.repositories.menu_repository import MenuRepository

logger = logging.getLogger(__name__)


class MenuService:

    @staticmethod
    def get_all(db: Session) -> list[MenuItem]:
        return MenuRepository.get_all(db)

    @staticmethod
    def create(db: Session, name: str, price: float, category: str,
               ingredients: str = "", instructions: str = "", cooking_time: int = 30) -> MenuItem:
        return MenuRepository.create(db, name, price, category, ingredients, instructions, cooking_time)

    @staticmethod
    def _get_or_404(db: Session, item_id: int) -> MenuItem:
        item = MenuRepository.get_by_id(db, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Menu item not found")
        return item

    @staticmethod
    def update(db: Session, item_id: int, name: str, price: float, category: str,
               ingredients: str = "", instructions: str = "", cooking_time: int = 30) -> MenuItem:
        item = MenuService._get_or_404(db, item_id)
        item.name = name
        item.price = price
        item.category = category
        item.ingredients = ingredients
        item.instructions = instructions
        item.cooking_time = cooking_time
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def delete(db: Session, item_id: int) -> dict:
        item = MenuService._get_or_404(db, item_id)
        MenuRepository.delete(db, item)
        return {"message": "Menu item deleted"}

    @staticmethod
    def get_by_id(db: Session, item_id: int) -> MenuItem:
        item = MenuRepository.get_by_id(db, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Menu item not found")
        return item