from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import admin_required, get_current_user
from app.models.user import User
from app.schemas.schemas import MenuItemCreate, MenuItemResponse, MenuItemUpdate
from app.services.menu_service import MenuService

router = APIRouter(prefix="/menu", tags=["Menu"])


@router.get("/", response_model=list[MenuItemResponse])
def get_menu(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return MenuService.get_all(db)


@router.post("/", response_model=MenuItemResponse)
def create_item(data: MenuItemCreate, db: Session = Depends(get_db), _: User = Depends(admin_required)):
    return MenuService.create(db, data.name, data.price, data.category)


@router.put("/{item_id}", response_model=MenuItemResponse)
def update_item(item_id: int, data: MenuItemUpdate, db: Session = Depends(get_db), _: User = Depends(admin_required)):
    return MenuService.update(db, item_id, data.name, data.price, data.category)


@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db), _: User = Depends(admin_required)):
    return MenuService.delete(db, item_id)