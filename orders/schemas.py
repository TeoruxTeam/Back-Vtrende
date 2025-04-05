from pydantic import BaseModel
from datetime import datetime


class OrderDTO(BaseModel):
    id: int
    created_at: datetime
    status: str
    total_price: float
    items: list

class GetSelfOrdersResponseSchema(BaseModel):
    data: list[OrderDTO]
    count: int

class CreateOrderResponseSchema(BaseModel):
    data: OrderDTO


