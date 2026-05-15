import logging
import os
from fastapi import Request, FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.core.database import Base, engine, SessionLocal
from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User
from app.templating import templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Импорт роутеров
from app.routers.pages import (
    auth_router, menu_router, tables_router, orders_router,
    kitchen_router, salary_router, admin_router
)

app = FastAPI(title="Restaurant Management System")

# Монтируем статику
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Настройка лимитера (в тестах можно отключить через переменную окружения)
if os.getenv("TESTING", "").lower() == "true":
    # Для тестов делаем лимитер очень большим или отключаем
    limiter = Limiter(key_func=get_remote_address, default_limits=["1000/minute"])
else:
    limiter = Limiter(key_func=get_remote_address, default_limits=["5/minute"])

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Подключаем роутеры
app.include_router(auth_router)
app.include_router(menu_router)
app.include_router(tables_router)
app.include_router(orders_router)
app.include_router(kitchen_router)
app.include_router(salary_router)
app.include_router(admin_router)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Создание таблиц
Base.metadata.create_all(bind=engine)

def create_admin_if_not_exists():
    db = SessionLocal()
    admin = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
    if not admin:
        admin = User(
            username=settings.ADMIN_USERNAME,
            password=hash_password(settings.ADMIN_PASSWORD),
            role="admin"
        )
        db.add(admin)
        db.commit()
        logging.info(f"Admin user '{settings.ADMIN_USERNAME}' created")
    else:
        logging.info(f"Admin user already exists")
    db.close()

@app.get("/")
async def root():
    return RedirectResponse(url="/pages")

@app.on_event("startup")
def startup_event():
    create_admin_if_not_exists()