from typing import List

from pydantic import BaseModel


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


class MenuItemUpdate(BaseModel):
    name: str
    price: float
    category: str


class MenuItemResponse(BaseModel):
    id: int
    name: str
    price: float
    category: str

    model_config = {"from_attributes": True}


# --- Order ---

class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int


class OrderCreate(BaseModel):
    table_id: int
    items: List[OrderItemCreate]


class OrderResponse(BaseModel):
    id: int
    user_id: int
    table_id: int
    status: str
    total_amount: float

    model_config = {"from_attributes": True}


# --- Analytics ---

class AnalyticsResponse(BaseModel):
    revenue: float
    status_stats: list
    top_dishes: list
    table_load: str