from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import admin_required, waiter_required, get_current_user
from app.services.menu_service import MenuService
from app.templating import templates
from app.utils.decorators import handle_errors
from app.models.user import User

router = APIRouter(prefix="/pages", tags=["Menu"])

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

@router.post("/menu/delete/{item_id}")
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