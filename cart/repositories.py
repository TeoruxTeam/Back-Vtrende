from core.repositories import BaseRepository
from cart.models import Cart
from items.models import Item
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from cart.schemas import CartDTO, CartItemDTO


class CartRepository(BaseRepository):

    async def add_to_cart(self, item_id: int, user_id: int) -> Item:
        async with self.get_session() as session:
            query = await session.execute(
                select(Cart).where(
                    Cart.item_id == item_id, 
                    Cart.user_id == user_id
                )
            )
            cart = query.scalar_one_or_none()
            if cart:
                cart.quantity += 1
            else:
                cart = Cart(item_id=item_id, user_id=user_id, quantity=1)
                session.add(cart)
            await session.commit()
            await session.refresh(cart)
            return CartDTO.model_validate(cart)

    async def get_cart(self, user_id: int, limit: int = 10, offset: int = 0) -> tuple[list[CartItemDTO], int, float]:
        async with self.get_session() as session:
            query = await session.execute(
                select(Cart).options(
                    selectinload(Cart.item)
                ).where(Cart.user_id == user_id)
                .order_by(Cart.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            carts = query.scalars().all()
            count_query = await session.execute(
                select(func.count(Cart)).where(Cart.user_id == user_id)
            )
            count = count_query.scalar()

            total_price_query = await session.execute(
                select(
                    func.sum(Cart.quantity * Item.price)
                )
                .join(Item, Cart.item_id == Item.id)
                .where(Cart.user_id == user_id)
            )
            total_price = total_price_query.scalar()
            
            return [CartItemDTO.model_validate(cart) for cart in carts], count, total_price

    async def decrease_item_quantity(self, item_id: int, user_id: int) -> None:
        async with self.get_session() as session:
            query = await session.execute(
                select(Cart).where(
                    Cart.item_id == item_id, Cart.user_id == user_id
                )
            )
            cart = query.scalar_one_or_none()
            if cart:
                cart.quantity -= 1
                if cart.quantity == 0:
                    await session.delete(cart)
                await session.commit()
                await session.refresh(cart)

    async def remove_from_cart(self, item_id: int, user_id: int) -> None:
        async with self.get_session() as session:
            query = await session.execute(
                select(Cart).where(Cart.item_id == item_id, Cart.user_id == user_id)
            )
            cart = query.scalar_one_or_none()
            if cart:
                await session.delete(cart)
                await session.commit()
                await session.refresh(cart)
