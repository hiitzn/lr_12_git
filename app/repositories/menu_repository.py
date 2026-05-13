from sqlalchemy.orm import Session

from app.models.menu import MenuItem


class MenuRepository:

    @staticmethod
    def get_all(db: Session) -> list[MenuItem]:
        return db.query(MenuItem).all()

    @staticmethod
    def get_by_id(db: Session, item_id: int) -> MenuItem | None:
        return db.query(MenuItem).filter(MenuItem.id == item_id).first()

    @staticmethod
    def create(db: Session, name: str, price: float, category: str) -> MenuItem:
        item = MenuItem(name=name, price=price, category=category)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def update(db: Session, item: MenuItem, name: str, price: float, category: str) -> MenuItem:
        item.name = name
        item.price = price
        item.category = category
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def delete(db: Session, item: MenuItem) -> None:
        db.delete(item)
        db.commit()