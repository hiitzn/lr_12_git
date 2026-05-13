from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.schemas import OrderResponse
from app.services.order_service import OrderService

router = APIRouter(prefix="/kitchen", tags=["Kitchen"])


@router.patch("/{order_id}", response_model=OrderResponse)
def update_status(
    order_id: int,
    status: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return OrderService.change_status(db, order_id, status)