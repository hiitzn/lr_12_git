import logging
from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    # bcrypt ограничение 72 байта
    password_bytes = password.encode('utf-8')[:72]
    return pwd_context.hash(password_bytes)


def verify_password(plain: str, hashed: str) -> bool:
    plain_bytes = plain.encode('utf-8')[:72]
    return pwd_context.verify(plain_bytes, hashed)


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except Exception as e:
        logger.warning("Token decode error: %s", e)
        return None