from core.repositories import BaseRepository
from orders.models import Order, OrderItem
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from cart.models import Cart
from orders.schemas import OrderDTO, OrderItemDTO


class OrderRepository(BaseRepository):
    
    async def create_order(self, user_id: int) -> int:
        async with self.get_session() as session:
            async with session.begin():
                cart_items = await session.execute(
                    select(Cart).options(
                        selectinload(Cart.item)
                    ).where(Cart.user_id == user_id)
                )
                cart_items = cart_items.scalars().all()

                order = Order(
                    user_id=user_id,
                    status="pending",
                    total_price=sum(
                        cart_item.quantity * cart_item.item.price
                        for cart_item in cart_items
                    ),
                )
                await session.add(order)
                await session.flush()
                order_items = [
                    OrderItem(
                        order_id=order.id,
                        item_id=cart_item.item_id,
                        quantity=cart_item.quantity,
                        price_at_time=cart_item.item.price
                    )
                    for cart_item in cart_items
                ]
                for order_item in order_items:
                    await session.add(order_item)

                await session.commit()
                await session.refresh(order)
                return order.id

    async def get_order_with_items(self, order_id: int) -> OrderDTO | None:
        async with self.get_session() as session:
            order = await session.execute(
                select(Order).options(
                    selectinload(Order.order_items)
                ).where(Order.id == order_id)
            )
            order = order.scalar_one_or_none()
            if order:
                return OrderDTO.model_validate(order)
            
    async def get_self_orders(self, user_id: int) -> list[OrderDTO]:
        async with self.get_session() as session:
            orders = await session.execute(
                select(Order).options(
                    selectinload(Order.order_items)
                ).where(Order.user_id == user_id)
            )
            return orders.scalars().all()