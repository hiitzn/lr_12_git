from fastapi.templating import Jinja2Templates
from markupsafe import escape

# Единый объект шаблонов
templates = Jinja2Templates(directory="app/templates")

def nl2br(value: str) -> str:
    """Безопасно экранирует HTML и заменяет \n на <br>"""
    if not value:
        return ""
    escaped = escape(value)
    return escaped.replace('\n', '<br>')

# Регистрация фильтра
templates.env.filters["nl2br"] = nl2br