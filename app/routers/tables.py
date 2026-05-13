from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import admin_required, get_current_user
from app.models.user import User
from app.schemas.schemas import TableCreate, TableResponse
from app.services.table_service import TableService

router = APIRouter(prefix="/tables", tags=["Tables"])


@router.get("/", response_model=list[TableResponse])
def get_tables(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return TableService.get_all(db)


@router.post("/", response_model=TableResponse)
def create_table(data: TableCreate, db: Session = Depends(get_db), _: User = Depends(admin_required)):
    return TableService.create(db, data.number, data.seats)


@router.patch("/{table_id}/occupy", response_model=TableResponse)
def occupy_table(table_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return TableService.occupy(db, table_id)


@router.patch("/{table_id}/free", response_model=TableResponse)
def free_table(table_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return TableService.free(db, table_id)


@router.delete("/{table_id}")
def delete_table(table_id: int, db: Session = Depends(get_db), _: User = Depends(admin_required)):
    TableService.delete(db, table_id)
    return {"message": "Table deleted"}