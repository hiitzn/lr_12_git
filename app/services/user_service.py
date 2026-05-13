import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

VALID_ROLES = {"user", "admin"}


class UserService:

    @staticmethod
    def get_all(db: Session) -> list[User]:
        return UserRepository.get_all(db)

    @staticmethod
    def change_role(db: Session, user_id: int, role: str) -> User:
        if role not in VALID_ROLES:
            raise HTTPException(status_code=400, detail=f"Invalid role. Valid: {VALID_ROLES}")
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        updated = UserRepository.update_role(db, user, role)
        logger.info("User %d role changed to %s", user_id, role)
        return updated