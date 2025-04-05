from cart.repositories import CartRepository
from cart.schemas import AddToCartResponseSchema, GetCartResponseSchema
from items.repositories import ItemRepository
from fastapi import HTTPException


class CartService:
    def __init__(self, cart_repository: CartRepository, item_repository: ItemRepository):
        self.cart_repository = cart_repository
        self.item_repository = item_repository

    async def add_to_cart(
        self, item_id: int, user_id: int
    ) -> AddToCartResponseSchema:
        item = await self.item_repository.get_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        cart_item = await self.cart_repository.add_to_cart(item_id, user_id)
        return AddToCartResponseSchema(data=cart_item)

    async def get_cart(
        self, user_id: int, limit: int = 10, offset: int = 0
    ) -> GetCartResponseSchema:
        cart_items, count, total_price = await self.cart_repository.get_cart(
            user_id, limit, offset
        )
        return GetCartResponseSchema(
            data=cart_items,
            total_price=total_price,
            total_count=count
        )
    
    async def decrease_item_quantity(
        self, item_id: int, user_id: int
    ) -> None:
        await self.cart_repository.decrease_item_quantity(item_id, user_id)

    async def remove_from_cart(
        self, item_id: int, user_id: int
    ) -> None:
        await self.cart_repository.remove_from_cart(item_id, user_id)

    async def create_order(
        self, user_id: int
    ) -> CreateOrderResponseSchema:
        await self.cart_repository.create_order(user_id)