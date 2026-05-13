from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.menu import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.table import RestaurantTable


class AnalyticsService:

    @staticmethod
    def get_dashboard(db: Session) -> dict:
        today = date.today()

        revenue = (
            db.query(func.sum(Order.total_amount))
            .filter(func.date(Order.created_at) == today)
            .scalar()
            or 0.0
        )

        status_stats = (
            db.query(Order.status, func.count(Order.id))
            .group_by(Order.status)
            .all()
        )

        top_dishes = (
            db.query(MenuItem.name, func.sum(OrderItem.quantity))
            .join(OrderItem, MenuItem.id == OrderItem.menu_item_id)
            .group_by(MenuItem.name)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(5)
            .all()
        )

        occupied = (
            db.query(func.count(RestaurantTable.id))
            .filter(RestaurantTable.occupied == True)
            .scalar()
        )
        total = db.query(func.count(RestaurantTable.id)).scalar()

        return {
            "revenue": revenue,
            "status_stats": status_stats,
            "top_dishes": top_dishes,
            "table_load": f"{occupied}/{total}",
        }