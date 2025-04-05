from pydantic import BaseModel


class OrderDTO(BaseModel):
    id: int
    created_at: datetime
    status: str
    total_price: float
    items: list

class GetSelfOrdersResponseSchema(BaseModel):
    data: list[OrderDTO]
    count: int
