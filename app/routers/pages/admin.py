from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import admin_required
from app.services.user_service import UserService
from app.services.analytics_service import AnalyticsService
from app.repositories.user_repository import UserRepository
from app.templating import templates
from app.utils.decorators import handle_errors
from app.models.user import User

router = APIRouter(prefix="/pages", tags=["Admin"])

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

@router.post("/admin/users/{user_id}/hourly_rate")
@handle_errors(redirect_url="/pages/admin")
async def update_hourly_rate(
    user_id: int,
    hourly_rate: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    UserService.update_hourly_rate(db, user_id, hourly_rate)
    return RedirectResponse(url="/pages/admin?success=Ставка+изменена", status_code=302)

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