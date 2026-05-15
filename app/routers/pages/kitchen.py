from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import cook_required
from app.services.order_service import OrderService
from app.templating import templates
from app.utils.decorators import handle_errors
from app.models.user import User

router = APIRouter(prefix="/pages", tags=["Kitchen"])

# ------------------- КУХНЯ -------------------
@router.get("/kitchen")
async def kitchen_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(cook_required),
    error: str = None,
    success: str = None,
):
    orders = OrderService.get_kitchen_orders_with_details(db)
    return templates.TemplateResponse("kitchen.html", {
        "request": request,
        "orders": orders,
        "current_user": user,
        "error": error,
        "success": success
    })

@router.post("/kitchen/{order_id}/status")
@handle_errors(redirect_url="/pages/kitchen")
async def kitchen_change_status(
    order_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(cook_required)
):
    if status not in ["cooking", "ready"]:
        raise HTTPException(403, "Повар может менять статус только на 'Готовится' или 'Готов'")
    OrderService.change_status(db, order_id, status)
    return RedirectResponse(url="/pages/kitchen?success=Статус+изменён", status_code=302)

@router.get("/kitchen/history")
async def kitchen_history(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(cook_required),
    error: str = None,
    success: str = None,
):
    daily_stats = OrderService.get_orders_grouped_by_date(db, user_id=None)
    return templates.TemplateResponse("orders_history.html", {
        "request": request,
        "daily_stats": daily_stats,
        "current_user": user,
        "title": "История заказов (кухня)",
        "error": error,
        "success": success
    })