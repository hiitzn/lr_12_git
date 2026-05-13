import logging
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

logger = logging.getLogger(__name__)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Возвращает пользователя или None, если не авторизован (для страниц входа/регистрации)"""
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == int(user_id)).first()
    return user

def admin_required(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def waiter_required(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ["waiter", "admin"]:
        raise HTTPException(status_code=403, detail="Only waiters and admins allowed")
    return current_user

def cook_required(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ["cook", "admin"]:
        raise HTTPException(status_code=403, detail="Only cooks and admins allowed")
    return current_user