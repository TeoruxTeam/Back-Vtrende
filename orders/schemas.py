from pydantic import BaseModel, ConfigDict
from datetime import datetime
from orders.models import OrderItem


class OrderItemDTO(BaseModel):
    id: int
    item_id: int
    order_id: int
    quantity: int
    price_at_time: float

    model_config = ConfigDict(from_attributes=True)
        

class OrderDTO(BaseModel):
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    total_price: float

    order_items: list[OrderItemDTO]

    model_config = ConfigDict(from_attributes=True)


class GetSelfOrdersResponseSchema(BaseModel):
    data: list[OrderDTO]
    count: int


class CreateOrderResponseSchema(BaseModel):
    data: OrderDTO
    message: str = "success.order.created"


