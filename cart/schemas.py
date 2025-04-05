from pydantic import BaseModel, ConfigDict
from items.schemas import ItemDTO
from datetime import datetime
from orders.schemas import OrderDTO


class CartDTO(BaseModel):
    id: int
    item_id: int
    user_id: int
    quantity: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AddToCartResponseSchema(BaseModel):
    data: CartDTO
    message: str = "success.cart.item_added"


class CartItemDTO(BaseModel):
    id: int
    quantity: int
    item: ItemDTO


class GetCartResponseSchema(BaseModel):
    data: list[CartItemDTO]
    total_price: float


