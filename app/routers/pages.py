from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, date

from app.core.database import get_db
from app.core.dependencies import (
    get_current_user, admin_required, get_current_user_optional,
    waiter_required, cook_required
)
from app.models.user import User
from app.services.menu_service import MenuService
from app.services.table_service import TableService
from app.services.order_service import OrderService
from app.services.analytics_service import AnalyticsService
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.services.table_booking_service import TableBookingService
from app.services.work_log_service import WorkLogService
from app.repositories.user_repository import UserRepository
from app.repositories.table_repository import TableRepository
from app.repositories.table_booking_repository import TableBookingRepository
from app.utils.form_parsers import parse_order_items
from app.templating import templates
from app.utils.decorators import handle_errors   # импорт декоратора

router = APIRouter(prefix="/pages", tags=["Pages"])

# ------------------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ -------------------
def _render_orders_list(request: Request, orders, user: User, title: str, show_all: bool, error: str = None, success: str = None):
    return templates.TemplateResponse("orders_list.html", {
        "request": request,
        "orders": orders,
        "current_user": user,
        "title": title,
        "show_all": show_all,
        "error": error,
        "success": success
    })

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
@handle_errors(redirect_url="/pages/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    AuthService.register(db, username, password)
    return RedirectResponse(url="/pages/login?success=Регистрация+успешна", status_code=302)

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/pages/login", status_code=302)
    response.delete_cookie("access_token")
    return response

# ------------------- МЕНЮ -------------------
@router.get("/menu")
async def menu_list(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(waiter_required),
    error: str = None,
    success: str = None,
):
    items = MenuService.get_all(db)
    return templates.TemplateResponse("menu_list.html", {
        "request": request,
        "items": items,
        "current_user": user,
        "error": error,
        "success": success
    })

@router.get("/menu/create")
async def menu_create_form(
    request: Request,
    user: User = Depends(admin_required),
    error: str = None,
    success: str = None,
):
    return templates.TemplateResponse("menu_form.html", {
        "request": request,
        "current_user": user,
        "error": error,
        "success": success
    })

@router.post("/menu/create")
@handle_errors(redirect_url="/pages/menu")
async def menu_create(
    name: str = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    ingredients: str = Form(""),
    instructions: str = Form(""),
    cooking_time: int = Form(30),
    db: Session = Depends(get_db),
    user: User = Depends(admin_required)
):
    MenuService.create(db, name, price, category, ingredients, instructions, cooking_time)
    return RedirectResponse(url="/pages/menu?success=Блюдо+добавлено", status_code=302)

@router.get("/menu/edit/{item_id}")
async def menu_edit_form(
    request: Request,
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(admin_required),
    error: str = None,
    success: str = None,
):
    item = MenuService.get_by_id(db, item_id)
    return templates.TemplateResponse("menu_form.html", {
        "request": request,
        "item": item,
        "current_user": user,
        "error": error,
        "success": success
    })

@router.post("/menu/edit/{item_id}")
@handle_errors(redirect_url="/pages/menu")
async def menu_edit(
    item_id: int,
    name: str = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    ingredients: str = Form(""),
    instructions: str = Form(""),
    cooking_time: int = Form(30),
    db: Session = Depends(get_db),
    user: User = Depends(admin_required)
):
    MenuService.update(db, item_id, name, price, category, ingredients, instructions, cooking_time)
    return RedirectResponse(url="/pages/menu?success=Блюдо+обновлено", status_code=302)

@router.post("/menu/delete/{item_id}")   # ИЗМЕНЕНО: было GET
@handle_errors(redirect_url="/pages/menu")
async def menu_delete(item_id: int, db: Session = Depends(get_db), user: User = Depends(admin_required)):
    MenuService.delete(db, item_id)
    return RedirectResponse(url="/pages/menu?success=Блюдо+удалено", status_code=302)

# ------------------- РЕЦЕПТЫ (только просмотр) -------------------
@router.get("/recipes/{menu_item_id}")
async def recipe_detail(request: Request, menu_item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in ['cook', 'admin']:
        raise HTTPException(403, "Доступ только для поваров и админов")
    item = MenuService.get_by_id(db, menu_item_id)
    if not item:
        raise HTTPException(404, "Блюдо не найдено")
    return templates.TemplateResponse("recipe_detail.html", {
        "request": request,
        "item": item,
        "current_user": user
    })

# ------------------- СТОЛЫ -------------------
@router.get("/tables")
async def tables_list(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(waiter_required),
    error: str = None,
    success: str = None,
):
    tables = TableService.get_all_with_bookings(db)
    return templates.TemplateResponse("tables_list.html", {
        "request": request,
        "tables": tables,
        "current_user": user,
        "error": error,
        "success": success
    })

@router.get("/tables/create")
async def table_create_form(
    request: Request,
    user: User = Depends(admin_required),
    error: str = None,
    success: str = None,
):
    return templates.TemplateResponse("table_form.html", {
        "request": request,
        "current_user": user,
        "error": error,
        "success": success
    })

@router.post("/tables/create")
@handle_errors(redirect_url="/pages/tables")
async def table_create(
    number: int = Form(...),
    seats: int = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(admin_required)
):
    TableService.create(db, number, seats)
    return RedirectResponse(url="/pages/tables?success=Стол+добавлен", status_code=302)

@router.post("/tables/delete/{table_id}")   # ИЗМЕНЕНО: было GET
@handle_errors(redirect_url="/pages/tables")
async def table_delete(table_id: int, db: Session = Depends(get_db), user: User = Depends(admin_required)):
    TableService.delete(db, table_id)
    return RedirectResponse(url="/pages/tables?success=Стол+удалён", status_code=302)

@router.post("/tables/occupy/{table_id}")   # ИЗМЕНЕНО: было GET
@handle_errors(redirect_url="/pages/tables")
async def table_occupy(table_id: int, db: Session = Depends(get_db), user: User = Depends(waiter_required)):
    if TableBookingRepository.is_table_booked(db, table_id, datetime.utcnow()):
        raise HTTPException(400, "Стол забронирован на текущее время")
    TableService.occupy(db, table_id)
    return RedirectResponse(url="/pages/tables?success=Стол+занят", status_code=302)

@router.post("/tables/free/{table_id}")   # ИЗМЕНЕНО: было GET
@handle_errors(redirect_url="/pages/tables")
async def table_free(table_id: int, db: Session = Depends(get_db), user: User = Depends(waiter_required)):
    TableService.free(db, table_id)
    return RedirectResponse(url="/pages/tables?success=Стол+освобождён", status_code=302)

# ------------------- БРОНИРОВАНИЕ -------------------
@router.get("/tables/book/{table_id}")
async def book_table_form(
    request: Request,
    table_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(waiter_required),
    error: str = None,
    success: str = None,
):
    table = TableRepository.get_by_id(db, table_id)
    if not table:
        raise HTTPException(404, "Стол не найден")
    return templates.TemplateResponse("book_table.html", {
        "request": request,
        "table": table,
        "current_user": user,
        "now_date": date.today().isoformat(),
        "error": error,
        "success": success
    })

@router.post("/tables/book/{table_id}")
@handle_errors(redirect_url="/pages/tables")
async def book_table(
    request: Request,
    table_id: int,
    booking_date: str = Form(...),
    booking_time: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(waiter_required)
):
    try:
        booking_datetime = datetime.strptime(f"{booking_date} {booking_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(400, "Неверный формат даты или времени")
    TableBookingService.create_booking(db, user.id, table_id, booking_datetime)
    return RedirectResponse(url="/pages/tables?success=Стол+забронирован", status_code=302)

@router.get("/bookings")
async def view_bookings(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(waiter_required),
    error: str = None,
    success: str = None,
):
    bookings = TableBookingService.get_week_bookings(db)
    return templates.TemplateResponse("bookings.html", {
        "request": request,
        "bookings": bookings,
        "current_user": user,
        "error": error,
        "success": success
    })

@router.post("/bookings/{booking_id}/cancel")
@handle_errors(redirect_url="/pages/bookings")
async def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(waiter_required)
):
    is_admin = user.role == "admin"
    TableBookingService.cancel_booking(db, booking_id, user.id, is_admin)
    return RedirectResponse(url="/pages/bookings?success=Бронь+отменена", status_code=302)

@router.get("/bookings/history")
async def bookings_history(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(waiter_required),
    error: str = None,
    success: str = None,
):
    expired_bookings = TableBookingService.get_expired_bookings(db)
    return templates.TemplateResponse("bookings_history.html", {
        "request": request,
        "bookings": expired_bookings,
        "current_user": user,
        "error": error,
        "success": success
    })

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
    return _render_orders_list(request, orders, user, "Мои заказы (все)", False, error=error, success=success)

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

@router.post("/orders/delete/{order_id}")   # ИЗМЕНЕНО: было GET
@handle_errors(redirect_url="/pages/orders")
async def order_delete(order_id: int, db: Session = Depends(get_db), user: User = Depends(admin_required)):
    OrderService.delete(db, order_id)
    return RedirectResponse(url="/pages/orders?success=Заказ+удалён", status_code=302)

# ------------------- ЗАРПЛАТА И ЧАСЫ -------------------
@router.get("/add_hours")
async def add_hours_form(
    request: Request,
    user: User = Depends(waiter_required),
    error: str = None,
    success: str = None,
):
    return templates.TemplateResponse("add_hours.html", {
        "request": request,
        "current_user": user,
        "error": error,
        "success": success
    })

@router.post("/add_hours")
@handle_errors(redirect_url="/pages/add_hours")
async def add_hours(
    request: Request,
    hours: float = Form(...),
    date_str: str = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(waiter_required)
):
    if date_str:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        date_obj = datetime.utcnow()
    WorkLogService.add_hours(db, user.id, hours, date_obj)
    return RedirectResponse(url="/pages/my_salary?success=Часы+добавлены", status_code=302)

@router.get("/my_salary")
async def my_salary(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(waiter_required),
    error: str = None,
    success: str = None,
):
    total_hours = WorkLogService.get_user_hours(db, user.id)
    salary = total_hours * user.hourly_rate
    return templates.TemplateResponse("my_salary.html", {
        "request": request,
        "total_hours": total_hours,
        "hourly_rate": user.hourly_rate,
        "salary": salary,
        "current_user": user,
        "error": error,
        "success": success
    })

@router.get("/salary_stats")
async def salary_stats(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(admin_required),
    error: str = None,
    success: str = None,
):
    stats = UserService.get_users_with_salary_stats(db)
    return templates.TemplateResponse("salary_stats.html", {
        "request": request,
        "stats": stats,
        "current_user": user,
        "error": error,
        "success": success
    })

@router.post("/admin/users/{user_id}/hourly_rate")
@handle_errors(redirect_url="/pages/admin")
async def update_hourly_rate(
    user_id: int,
    hourly_rate: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    user = UserRepository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(404, "Пользователь не найден")
    user.hourly_rate = hourly_rate
    db.commit()
    return RedirectResponse(url="/pages/admin?success=Ставка+изменена", status_code=302)

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

# ------------------- АНАЛИТИКА -------------------
@router.get("/analytics")
async def analytics_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(admin_required),
    error: str = None,
    success: str = None,
):
    data = AnalyticsService.get_dashboard(db)
    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "current_user": user,
        "error": error,
        "success": success,
        **data
    })

# ------------------- АДМИН-ПАНЕЛЬ -------------------
@router.get("/admin")
async def admin_panel(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(admin_required),
    error: str = None,
    success: str = None,
):
    users = UserService.get_all(db)
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "users": users,
        "current_user": user,
        "error": error,
        "success": success
    })

@router.post("/admin/users/{user_id}/role")
@handle_errors(redirect_url="/pages/admin")
async def admin_change_role(
    user_id: int,
    role: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(admin_required)
):
    UserService.change_role(db, user_id, role)
    return RedirectResponse(url="/pages/admin?success=Роль+изменена", status_code=302)

@router.post("/admin/users/{user_id}/delete")
@handle_errors(redirect_url="/pages/admin")
async def admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    if user_id == current_user.id:
        raise HTTPException(400, "Нельзя удалить самого себя")
    UserService.delete_user(db, user_id)
    return RedirectResponse(url="/pages/admin?success=Пользователь+удалён", status_code=302)