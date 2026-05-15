from typing import List
from pydantic import BaseModel, Field
from datetime import datetime

# --- Auth ---

class RegisterSchema(BaseModel):
    username: str = Field(..., max_length=50, description="Имя пользователя")
    password: str = Field(..., max_length=100, description="Пароль")

class LoginSchema(BaseModel):
    username: str = Field(..., max_length=50)
    password: str = Field(..., max_length=100)

# --- User ---

class UserResponse(BaseModel):
    id: int
    username: str
    role: str

    model_config = {"from_attributes": True}


# --- Table ---

class TableCreate(BaseModel):
    number: int = Field(..., ge=1, description="Номер стола")
    seats: int = Field(..., ge=1, le=20, description="Количество мест")

class TableResponse(BaseModel):
    id: int
    number: int
    seats: int
    occupied: bool

    model_config = {"from_attributes": True}


# --- Menu ---

class MenuItemCreate(BaseModel):
    name: str = Field(..., max_length=100)
    price: float = Field(..., ge=0)
    category: str = Field(..., max_length=50)
    ingredients: str | None = Field(None, max_length=500)
    instructions: str | None = Field(None, max_length=2000)
    cooking_time: int = Field(30, ge=1, le=300)

class MenuItemUpdate(BaseModel):
    name: str = Field(..., max_length=100)
    price: float = Field(..., ge=0)
    category: str = Field(..., max_length=50)
    ingredients: str | None = Field(None, max_length=500)
    instructions: str | None = Field(None, max_length=2000)
    cooking_time: int = Field(30, ge=1, le=300)

class MenuItemResponse(BaseModel):
    id: int
    name: str
    price: float
    category: str
    ingredients: str | None = None
    instructions: str | None = None
    cooking_time: int = 30

    model_config = {"from_attributes": True}


# --- Order ---

class OrderItemCreate(BaseModel):
    menu_item_id: int = Field(..., ge=1)
    quantity: int = Field(..., ge=1, le=99)

class OrderCreate(BaseModel):
    table_id: int = Field(..., ge=1)
    items: List[OrderItemCreate]
    notes: str | None = Field(None, max_length=500)

class OrderResponse(BaseModel):
    id: int
    user_id: int
    table_id: int
    status: str
    total_amount: float
    notes: str | None = None

    model_config = {"from_attributes": True}


# --- Analytics ---

class AnalyticsResponse(BaseModel):
    revenue: float
    status_stats: list
    top_dishes: list
    table_load: str


# --- Bookings ---

class TableBookingCreate(BaseModel):
    table_id: int = Field(..., ge=1)
    booking_time: datetime
    duration_minutes: int = Field(120, ge=30, le=240)

class TableBookingResponse(BaseModel):
    id: int
    table_id: int
    user_id: int
    booking_time: datetime
    duration_minutes: int
    status: str
    created_at: datetime
    table_number: int | None = None
    username: str | None = None

    model_config = {"from_attributes": True}


# --- Work Log ---

class WorkLogCreate(BaseModel):
    user_id: int = Field(..., ge=1)
    hours: float = Field(..., ge=0, le=24)
    date: datetime | None = None

class WorkLogResponse(BaseModel):
    id: int
    user_id: int
    hours: float
    created_at: datetime   
    model_config = {"from_attributes": True}