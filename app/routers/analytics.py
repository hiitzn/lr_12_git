from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import admin_required
from app.models.user import User
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/")
def get_dashboard(db: Session = Depends(get_db), _: User = Depends(admin_required)):
    return AnalyticsService.get_dashboard(db)