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
from app.routers import admin, analytics, auth, kitchen, menu, orders, tables, users
from app.routers import pages
from app.templating import templates 

app = FastAPI(title="Restaurant Management System")

app.mount("/static", StaticFiles(directory="app/static"), name="static")


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tables.router)
app.include_router(menu.router)
app.include_router(orders.router)
app.include_router(kitchen.router)
app.include_router(admin.router)
app.include_router(analytics.router)
app.include_router(pages.router)

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

create_admin_if_not_exists()