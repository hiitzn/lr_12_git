import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class AuthService:

    @staticmethod
    def register(db: Session, username: str, password: str):
        if UserRepository.get_by_username(db, username):
            raise HTTPException(status_code=400, detail="Username already taken")
        # При регистрации создаём пользователя с ролью "waiter" (официант)
        user = UserRepository.create(db, username, hash_password(password), role="waiter")
        logger.info("New user registered: %s (role: waiter)", username)
        return user

    @staticmethod
    def login(db: Session, username: str, password: str) -> str:
        user = UserRepository.get_by_username(db, username)
        if not user or not verify_password(password, user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return create_access_token({"sub": str(user.id)})