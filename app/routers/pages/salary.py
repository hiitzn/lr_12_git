from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import waiter_required, admin_required
from app.services.work_log_service import WorkLogService
from app.templating import templates
from app.utils.decorators import handle_errors
from app.models.user import User

router = APIRouter(prefix="/pages", tags=["Salary"])

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