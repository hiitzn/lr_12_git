from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import admin_required
from app.models.user import User
from app.schemas.schemas import MenuItemCreate, MenuItemResponse, TableCreate, TableResponse, UserResponse
from app.services.menu_service import MenuService
from app.services.table_service import TableService
from app.services.user_service import UserService

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db), _: User = Depends(admin_required)):
    return UserService.get_all(db)


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def change_role(user_id: int, role: str, db: Session = Depends(get_db), _: User = Depends(admin_required)):
    return UserService.change_role(db, user_id, role)


@router.post("/tables", response_model=TableResponse)
def create_table(data: TableCreate, db: Session = Depends(get_db), _: User = Depends(admin_required)):
    return TableService.create(db, data.number, data.seats)


@router.post("/menu", response_model=MenuItemResponse)
def create_menu_item(data: MenuItemCreate, db: Session = Depends(get_db), _: User = Depends(admin_required)):
    return MenuService.create(db, data.name, data.price, data.category)