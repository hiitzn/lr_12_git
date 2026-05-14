from app.schemas.schemas import OrderItemCreate

def parse_order_items(form_data) -> list[OrderItemCreate]:
    """
    Извлекает из данных формы список позиций заказа.
    Ожидает поля вида item_<id> и quantity_<id>.
    """
    items = []
    for key, value in form_data.items():
        if key.startswith("item_"):
            menu_item_id = int(key.split("_")[1])
            quantity_key = f"quantity_{menu_item_id}"
            quantity = int(form_data.get(quantity_key, 1))
            if quantity > 0:
                items.append(OrderItemCreate(menu_item_id=menu_item_id, quantity=quantity))
    return items