from fastapi import Request
from app.templating import templates
from app.models.user import User

def render_orders_list(request: Request, orders, user: User, title: str, show_all: bool, error: str = None, success: str = None):
    return templates.TemplateResponse("orders_list.html", {
        "request": request,
        "orders": orders,
        "current_user": user,
        "title": title,
        "show_all": show_all,
        "error": error,
        "success": success
    })