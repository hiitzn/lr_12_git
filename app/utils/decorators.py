import logging
from functools import wraps
from fastapi import HTTPException
from fastapi.responses import RedirectResponse

logger = logging.getLogger(__name__)

def handle_errors(redirect_url: str):
    """
    Декоратор для POST-обработчиков pages.
    При возникновении HTTPException делает редирект на redirect_url с параметром error
    и записывает ошибку в лог.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException as e:
                logger.exception(f"Error in {func.__name__}: {e.detail}")
                return RedirectResponse(url=f"{redirect_url}?error={e.detail}", status_code=302)
        return wrapper
    return decorator