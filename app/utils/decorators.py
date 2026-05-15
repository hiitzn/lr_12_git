import logging
from functools import wraps
from fastapi import HTTPException
from fastapi.responses import RedirectResponse

logger = logging.getLogger(__name__)

def handle_errors(redirect_url: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException as e:
                logger.warning(f"HTTPException in {func.__name__}: {e.detail}")
                return RedirectResponse(url=f"{redirect_url}?error={e.detail}", status_code=302)
            except Exception as e:
                logger.exception(f"Unexpected error in {func.__name__}: {str(e)}")
                return RedirectResponse(url=f"{redirect_url}?error=Внутренняя ошибка сервера", status_code=302)
        return wrapper
    return decorator