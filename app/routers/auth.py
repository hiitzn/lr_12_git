from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schemas import LoginSchema, RegisterSchema, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse)
def register(data: RegisterSchema, db: Session = Depends(get_db)):
    user = AuthService.register(db, data.username, data.password)
    return user


@router.post("/login")
def login(data: LoginSchema, response: Response, db: Session = Depends(get_db)):
    token = AuthService.login(db, data.username, data.password)
    response.set_cookie(key="access_token", value=token, httponly=True, samesite="lax")
    return {"message": "Logged in successfully"}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}