from orders.repositories import OrderRepository
from orders.schemas import GetSelfOrdersResponseSchema
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