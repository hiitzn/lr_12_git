from typing import List

from pydantic import BaseModel
from datetime import datetime

# --- Auth ---

class RegisterSchema(BaseModel):
    username: str
    password: str


class LoginSchema(BaseModel):
    username: str
    password: str


# --- User ---

class UserResponse(BaseModel):
    id: int
    username: str
    role: str

    model_config = {"from_attributes": True}


# --- Table ---

class TableCreate(BaseModel):
    number: int
    seats: int


class TableResponse(BaseModel):
    id: int
    number: int
    seats: int
    occupied: bool

    model_config = {"from_attributes": True}


# --- Menu ---

class MenuItemCreate(BaseModel):
    name: str
    price: float
    category: str
    ingredients: str | None = None
    instructions: str | None = None
    cooking_time: int = 30


class MenuItemUpdate(BaseModel):
    name: str
    price: float
    category: str
    ingredients: str | None = None
    instructions: str | None = None
    cooking_time: int = 30


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
    menu_item_id: int
    quantity: int


class OrderCreate(BaseModel):
    table_id: int
    items: List[OrderItemCreate]
    notes: str | None = None   # добавить


class OrderResponse(BaseModel):
    id: int
    user_id: int
    table_id: int
    status: str
    total_amount: float
    notes: str | None = None   # добавить
    model_config = {"from_attributes": True}


# --- Analytics ---

class AnalyticsResponse(BaseModel):
    revenue: float
    status_stats: list
    top_dishes: list
    table_load: str


class TableBookingCreate(BaseModel):
    table_id: int
    booking_time: datetime
    duration_minutes: int = 120

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

class WorkLogCreate(BaseModel):
    user_id: int
    hours: float
    date: datetime | None = None

class WorkLogResponse(BaseModel):
    id: int
    user_id: int
    hours: float
    date: datetime
    model_config = {"from_attributes": True}

class RecipeCreate(BaseModel):
    menu_item_id: int
    ingredients: str
    instructions: str
    cooking_time: int = 30

class RecipeResponse(BaseModel):
    id: int
    menu_item_id: int
    ingredients: str
    instructions: str
    cooking_time: int
    menu_item_name: str | None = None

    model_config = {"from_attributes": True}

class RecipeUpdate(BaseModel):
    ingredients: str | None = None
    instructions: str | None = None
    cooking_time: int | None = None