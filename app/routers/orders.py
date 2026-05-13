from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import admin_required, get_current_user
from app.models.user import User
from app.repositories.order_repository import OrderRepository
from app.schemas.schemas import OrderCreate, OrderResponse
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse)
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return OrderService.create(db, current_user.id, data.table_id, data.items)


@router.get("/", response_model=list[OrderResponse])
def get_orders(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return OrderRepository.get_all(db)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    from fastapi import HTTPException
    order = OrderRepository.get_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.delete("/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db), _: User = Depends(admin_required)):
    return OrderService.delete(db, order_id)