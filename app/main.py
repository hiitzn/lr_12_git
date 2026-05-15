import logging
from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.database import Base, engine, SessionLocal   
from app.core.config import settings                        
from app.core.security import hash_password               
from app.models.user import User                            
from app.routers import pages
from app.templating import templates 
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


app = FastAPI(title="Restaurant Management System")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
limiter = Limiter(key_func=get_remote_address, default_limits=["5/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

from app.routers.pages import (
    auth_router, menu_router, tables_router, orders_router,
    kitchen_router, salary_router, admin_router
)

app.include_router(auth_router)
app.include_router(menu_router)
app.include_router(tables_router)
app.include_router(orders_router)
app.include_router(kitchen_router)
app.include_router(salary_router)
app.include_router(admin_router)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

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