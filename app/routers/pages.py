from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.repositories.user_repository import UserRepository
from app.core.database import get_db
from app.core.dependencies import get_current_user, admin_required, get_current_user_optional, waiter_required, cook_required
from app.models.user import User
from app.models.order import Order
from app.services.menu_service import MenuService
from app.services.table_service import TableService
from app.services.order_service import OrderService
from app.services.analytics_service import AnalyticsService
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.schemas.schemas import OrderItemCreate
from sqlalchemy.orm import joinedload
from app.models.order_item import OrderItem

router = APIRouter(prefix="/pages", tags=["Pages"])
templates = Jinja2Templates(directory="app/templates")

# ------------------- ГЛАВНАЯ -------------------
@router.get("/")
async def home(request: Request, user: User | None = Depends(get_current_user_optional)):
    if user:
        if user.role == "cook":
            return RedirectResponse(url="/pages/kitchen", status_code=302)
        else:
            return RedirectResponse(url="/pages/menu", status_code=302)
    return templates.TemplateResponse("home.html", {"request": request, "current_user": None})

# ------------------- АУТЕНТИФИКАЦИЯ -------------------
@router.get("/login")
async def login_page(request: Request, user: User | None = Depends(get_current_user_optional)):
    if user:
        return RedirectResponse(url="/pages/menu", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "current_user": None})

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        token = AuthService.login(db, username, password)
        # Получаем пользователя, чтобы узнать его роль
        user = UserRepository.get_by_username(db, username)
        response = RedirectResponse(
            url="/pages/kitchen" if user and user.role == "cook" else "/pages/menu",
            status_code=302
        )
        response.set_cookie(key="access_token", value=token, httponly=True, samesite="lax")
        return response
    except HTTPException:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Неверное имя пользователя или пароль",
            "current_user": None
        })

@router.get("/register")
async def register_page(request: Request, user: User | None = Depends(get_current_user_optional)):
    if user:
        return RedirectResponse(url="/pages/menu", status_code=302)
    return templates.TemplateResponse("register.html", {"request": request, "current_user": None})

@router.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        AuthService.register(db, username, password)
        return RedirectResponse(url="/pages/login", status_code=302)
    except HTTPException as e:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": e.detail,
            "current_user": None
        })

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/pages/login", status_code=302)
    response.delete_cookie("access_token")
    return response

# ------------------- МЕНЮ (официанты и админы) -------------------
@router.get("/menu")
async def menu_list(request: Request, db: Session = Depends(get_db), user: User = Depends(waiter_required)):
    items = MenuService.get_all(db)
    return templates.TemplateResponse("menu_list.html", {"request": request, "items": items, "current_user": user})

@router.get("/menu/create")
async def menu_create_form(request: Request, user: User = Depends(admin_required)):
    return templates.TemplateResponse("menu_form.html", {"request": request, "current_user": user})

@router.post("/menu/create")
async def menu_create(
    name: str = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(admin_required)
):
    MenuService.create(db, name, price, category)
    return RedirectResponse(url="/pages/menu", status_code=302)

@router.get("/menu/edit/{item_id}")
async def menu_edit_form(request: Request, item_id: int, db: Session = Depends(get_db), user: User = Depends(admin_required)):
    item = MenuService.get_by_id(db, item_id)
    return templates.TemplateResponse("menu_form.html", {"request": request, "item": item, "current_user": user})

@router.post("/menu/edit/{item_id}")
async def menu_edit(
    item_id: int,
    name: str = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(admin_required)
):
    MenuService.update(db, item_id, name, price, category)
    return RedirectResponse(url="/pages/menu", status_code=302)

@router.get("/menu/delete/{item_id}")
async def menu_delete(item_id: int, db: Session = Depends(get_db), user: User = Depends(admin_required)):
    MenuService.delete(db, item_id)
    return RedirectResponse(url="/pages/menu", status_code=302)

# ------------------- СТОЛЫ (официанты и админы) -------------------
@router.get("/tables")
async def tables_list(request: Request, db: Session = Depends(get_db), user: User = Depends(waiter_required)):
    tables = TableService.get_all(db)
    return templates.TemplateResponse("tables_list.html", {"request": request, "tables": tables, "current_user": user})

@router.get("/tables/create")
async def table_create_form(request: Request, user: User = Depends(admin_required)):
    return templates.TemplateResponse("table_form.html", {"request": request, "current_user": user})

@router.post("/tables/create")
async def table_create(
    number: int = Form(...),
    seats: int = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(admin_required)
):
    TableService.create(db, number, seats)
    return RedirectResponse(url="/pages/tables", status_code=302)

@router.get("/tables/delete/{table_id}")
async def table_delete(table_id: int, db: Session = Depends(get_db), user: User = Depends(admin_required)):
    TableService.delete(db, table_id)
    return RedirectResponse(url="/pages/tables", status_code=302)

@router.get("/tables/occupy/{table_id}")
async def table_occupy(table_id: int, db: Session = Depends(get_db), user: User = Depends(waiter_required)):
    TableService.occupy(db, table_id)
    return RedirectResponse(url="/pages/tables", status_code=302)

@router.get("/tables/free/{table_id}")
async def table_free(table_id: int, db: Session = Depends(get_db), user: User = Depends(waiter_required)):
    TableService.free(db, table_id)
    return RedirectResponse(url="/pages/tables", status_code=302)

# ------------------- ЗАКАЗЫ (официанты и админы) -------------------
@router.get("/orders")
async def orders_list(request: Request, db: Session = Depends(get_db), user: User = Depends(waiter_required)):
    if user.role == "admin":
        orders = OrderService.get_all_orders(db)
    else:
        orders = OrderService.get_orders_for_user(db, user.id)
    # Подгружаем позиции для отображения блюд
    for order in orders:
        _ = order.items
    return templates.TemplateResponse("orders_list.html", {"request": request, "orders": orders, "current_user": user})

@router.get("/orders/create")
async def order_create_form(request: Request, db: Session = Depends(get_db), user: User = Depends(waiter_required)):
    tables = TableService.get_all(db)
    menu_items = MenuService.get_all(db)
    return templates.TemplateResponse("order_form.html", {"request": request, "tables": tables, "menu_items": menu_items, "current_user": user})

@router.post("/orders/create")
async def order_create(
    request: Request,
    table_id: int = Form(...),
    notes: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(waiter_required)
):
    form_data = await request.form()
    items = []
    for key, value in form_data.items():
        if key.startswith("item_"):
            menu_item_id = int(key.split("_")[1])
            quantity_key = f"quantity_{menu_item_id}"
            quantity = int(form_data.get(quantity_key, 1))
            if quantity > 0:
                items.append(OrderItemCreate(menu_item_id=menu_item_id, quantity=quantity))
    if not items:
        raise HTTPException(400, "Заказ должен содержать хотя бы одно блюдо")
    OrderService.create(db, user.id, table_id, items, notes=notes)
    return RedirectResponse(url="/pages/orders", status_code=302)

@router.get("/orders/status/{order_id}")
async def order_status_form(request: Request, order_id: int, db: Session = Depends(get_db), user: User = Depends(waiter_required)):
    order = OrderService.get_by_id(db, order_id)
    if not order:
        raise HTTPException(404)
    return templates.TemplateResponse("order_status.html", {"request": request, "order": order, "current_user": user})

@router.post("/orders/status/{order_id}")
async def order_status_update(
    order_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(waiter_required)
):
    OrderService.change_status(db, order_id, status)
    return RedirectResponse(url="/pages/orders", status_code=302)

@router.get("/orders/delete/{order_id}")
async def order_delete(order_id: int, db: Session = Depends(get_db), user: User = Depends(admin_required)):
    OrderService.delete(db, order_id)
    return RedirectResponse(url="/pages/orders", status_code=302)

# ------------------- КУХНЯ (повара и админы) -------------------
@router.get("/kitchen")
async def kitchen_page(request: Request, db: Session = Depends(get_db), user: User = Depends(cook_required)):
    orders = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.menu_item),
        joinedload(Order.user) 
    ).filter(Order.status.in_(["new", "cooking", "ready"])).order_by(Order.created_at).all()
    return templates.TemplateResponse("kitchen.html", {"request": request, "orders": orders, "current_user": user})

@router.post("/kitchen/{order_id}/status")
async def kitchen_change_status(
    order_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(cook_required)
):
    OrderService.change_status(db, order_id, status)
    return RedirectResponse(url="/pages/kitchen", status_code=302)

# ------------------- АНАЛИТИКА (только админ) -------------------
@router.get("/analytics")
async def analytics_dashboard(request: Request, db: Session = Depends(get_db), user: User = Depends(admin_required)):
    data = AnalyticsService.get_dashboard(db)
    return templates.TemplateResponse("analytics.html", {"request": request, "current_user": user, **data})

# ------------------- АДМИН-ПАНЕЛЬ (только админ) -------------------
@router.get("/admin")
async def admin_panel(request: Request, db: Session = Depends(get_db), user: User = Depends(admin_required)):
    users = UserService.get_all(db)
    return templates.TemplateResponse("admin.html", {"request": request, "users": users, "current_user": user})

@router.post("/admin/users/{user_id}/role")
async def admin_change_role(user_id: int, role: str = Form(...), db: Session = Depends(get_db), user: User = Depends(admin_required)):
    UserService.change_role(db, user_id, role)
    return RedirectResponse(url="/pages/admin", status_code=302)