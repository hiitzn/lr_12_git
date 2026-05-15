from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import waiter_required, admin_required, get_current_user
from app.services.order_service import OrderService
from app.services.table_service import TableService
from app.services.menu_service import MenuService
from app.utils.form_parsers import parse_order_items
from app.templating import templates
from app.utils.decorators import handle_errors
from app.routers.pages.utils import render_orders_list
from app.models.user import User

router = APIRouter(prefix="/pages", tags=["Orders"])

# ------------------- ЗАКАЗЫ -------------------
@router.get("/orders")
async def my_orders(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(waiter_required),
    error: str = None,
    success: str = None,
):
    orders = OrderService.get_orders_with_items(db, user_id=user.id, exclude_statuses=["paid"])
    return render_orders_list(request, orders, user, "Мои заказы (все)", False, error=error, success=success)

@router.get("/orders/history")
async def orders_history(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    error: str = None,
    success: str = None,
):
    if user.role == "admin":
        user_id = None
    elif user.role == "cook":
        user_id = None
    else:
        user_id = user.id
    daily_stats = OrderService.get_orders_grouped_by_date(db, user_id=user_id)
    return templates.TemplateResponse("orders_history.html", {
        "request": request,
        "daily_stats": daily_stats,
        "current_user": user,
        "title": "История заказов",
        "error": error,
        "success": success
    })

@router.get("/orders/create")
async def order_create_form(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(waiter_required),
    error: str = None,
    success: str = None,
):
    tables = TableService.get_all(db)
    menu_items = MenuService.get_all(db)
    return templates.TemplateResponse("order_form.html", {
        "request": request,
        "tables": tables,
        "menu_items": menu_items,
        "current_user": user,
        "error": error,
        "success": success
    })

@router.post("/orders/create")
@handle_errors(redirect_url="/pages/orders/create")
async def order_create(
    request: Request,
    table_id: int = Form(...),
    notes: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(waiter_required)
):
    form_data = await request.form()
    items = parse_order_items(form_data)
    if not items:
        raise HTTPException(400, "Заказ должен содержать хотя бы одно блюдо")
    OrderService.create(db, user.id, table_id, items, notes=notes)
    return RedirectResponse(url="/pages/orders?success=Заказ+создан", status_code=302)

@router.get("/orders/status/{order_id}")
async def order_status_form(
    request: Request,
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    from_history: bool = False,
    error: str = None,
):
    if user.role == "cook":
        raise HTTPException(403, "Повар может изменять статусы только на странице кухни")
    order = OrderService.get_by_id(db, order_id)
    allowed_statuses = OrderService.get_allowed_statuses_for_role(user.role)
    if user.role == "waiter" and order.user_id != user.id:
        raise HTTPException(403, "Вы можете изменять статус только своих заказов")
    return templates.TemplateResponse("order_status.html", {
        "request": request,
        "order": order,
        "current_user": user,
        "from_history": from_history,
        "allowed_statuses": allowed_statuses,
        "error": error
    })

@handle_errors(redirect_url="/pages/orders")
@router.post("/orders/status/{order_id}")
async def order_status_update(
    request: Request,
    order_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    allowed = OrderService.get_allowed_statuses_for_role(user.role)
    if status not in allowed:
        raise HTTPException(403, f"Роль '{user.role}' не может установить статус '{status}'")
    if user.role == "waiter":
        order = OrderService.get_by_id(db, order_id)
        if order.user_id != user.id:
            raise HTTPException(403, "Можно менять статус только своих заказов")
    OrderService.change_status(db, order_id, status)
    from_history = request.query_params.get("from_history") == "true"
    redirect_url = "/pages/orders/history" if from_history else "/pages/orders"
    success_msg = "Статус заказа изменён"
    return RedirectResponse(url=f"{redirect_url}?success={success_msg}", status_code=302)

@router.post("/orders/delete/{order_id}")
@handle_errors(redirect_url="/pages/orders")
async def order_delete(order_id: int, db: Session = Depends(get_db), user: User = Depends(admin_required)):
    OrderService.delete(db, order_id)
    return RedirectResponse(url="/pages/orders?success=Заказ+удалён", status_code=302)