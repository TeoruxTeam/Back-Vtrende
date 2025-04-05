from orders.repositories import OrderRepository
from orders.schemas import GetSelfOrdersResponseSchema, CreateOrderResponseSchema
from users.schemas import UserDTO


class OrderService:
    def __init__(self, repo: OrderRepository):
        self.repo = repo

    async def get_self_orders(self, user: UserDTO) -> GetSelfOrdersResponseSchema:
        orders, count = await self.repo.get_self_orders(user)
        return GetSelfOrdersResponseSchema(
            data=orders,
            count=count
        )
    
    async def create_order(self, user_id: int) -> CreateOrderResponseSchema:
        order_id = await self.repo.create_order(user_id)
        order_with_items = await self.repo.get_order_with_items(order_id)
        return CreateOrderResponseSchema(
            data=order_with_items
        )
