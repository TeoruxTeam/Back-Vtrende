from favorites.schemas import (
    AddItemToFavoritesResponseSchema,
    AddShopToFavoritesResponseSchema,
    GetFavoriteItemsResponseSchema,
    GetFavoriteShopsResponseSchema
)
from users.schemas import UserDTO
from favorites.repositories import FavoriteRepository
from items.repositories import ItemRepository
from users.repositories import UserRepository
from fastapi import HTTPException


class FavoriteService:
    def __init__(
        self, 
        fav_repo: FavoriteRepository,
        item_repo: ItemRepository,
        user_repo: UserRepository
    ):
        self.fav_repo = fav_repo
        self.item_repo = item_repo
        self.user_repo = user_repo

    async def add_item_to_favorites(self, item_id: int, user_id: int) -> AddItemToFavoritesResponseSchema:
        item = await self.item_repo.get_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="error.item.not_found")
        favorite = await self.fav_repo.add_item(item_id, user_id)
        return AddItemToFavoritesResponseSchema(
            data=favorite
        )
    
    async def add_shop_to_favorites(self, shop_id: int, user_id: int) -> AddShopToFavoritesResponseSchema:
        shop = await self.user_repo.get_user_by_id(shop_id)
        if not shop:
            raise HTTPException(status_code=404, detail="error.shop.not_found")
        favorite = await self.fav_repo.add_shop(shop_id, user_id)
        return AddShopToFavoritesResponseSchema(data=favorite)

    async def get_favorite_items(
        self, user_id: int, limit: int = 10, 
        offset: int = 0, search: str | None = None
    ) -> GetFavoriteItemsResponseSchema:
        favorites, count = await self.fav_repo.get_favorite_items(
            user_id, limit, offset, search
        )
        return GetFavoriteItemsResponseSchema(
            data=favorites, count=count
        )

    async def get_favorite_shops(
        self, user_id: int, limit: int = 10, 
        offset: int = 0, search: str | None = None
    ) -> GetFavoriteShopsResponseSchema:
        favorites, count = await self.fav_repo.get_favorite_shops(
            user_id, limit, offset, search
        )
        return GetFavoriteShopsResponseSchema(
            data=favorites, count=count
        )
    
    async def remove_item_from_favorites(self, item_id: int, user_id: int) -> None:
        await self.fav_repo.remove_item(item_id, user_id)

    async def remove_shop_from_favorites(self, shop_id: int, user_id: int) -> None:
        await self.fav_repo.remove_shop(shop_id, user_id)
