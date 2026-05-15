from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import update
from datetime import datetime, date

from app.core.database import get_db
from app.core.dependencies import waiter_required, admin_required, get_current_user
from app.models.table import RestaurantTable
from app.services.table_service import TableService
from app.services.table_booking_service import TableBookingService
from app.repositories.table_repository import TableRepository
from app.repositories.table_booking_repository import TableBookingRepository
from app.templating import templates
from app.utils.decorators import handle_errors
from app.models.user import User

router = APIRouter(prefix="/pages", tags=["Tables"])

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

@router.post("/tables/delete/{table_id}")
@handle_errors(redirect_url="/pages/tables")
async def table_delete(table_id: int, db: Session = Depends(get_db), user: User = Depends(admin_required)):
    TableService.delete(db, table_id)
    return RedirectResponse(url="/pages/tables?success=Стол+удалён", status_code=302)

@router.post("/tables/occupy/{table_id}")
async def table_occupy(table_id: int, db: Session = Depends(get_db), user: User = Depends(waiter_required)):
    result = db.execute(
        update(RestaurantTable)
        .where(RestaurantTable.id == table_id, RestaurantTable.occupied == False)
        .values(occupied=True)
    )
    if result.rowcount == 0:
        table_exists = db.query(RestaurantTable).filter(RestaurantTable.id == table_id).first()
        if not table_exists:
            raise HTTPException(404, "Стол не найден")
        else:
            raise HTTPException(400, "Стол уже занят")
    db.commit()
    return RedirectResponse(url="/pages/tables?success=Стол+занят", status_code=302)

@router.post("/tables/free/{table_id}")
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