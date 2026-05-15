from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_optional
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.templating import templates
from app.utils.decorators import handle_errors
from app.models.user import User

router = APIRouter(prefix="/pages", tags=["Auth"])

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
        response.set_cookie(key="access_token", value=token, httponly=True, samesite="strict", secure=True)
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