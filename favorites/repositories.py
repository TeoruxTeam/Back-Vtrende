from core.repositories import BaseRepository
from favorites.models import FavoriteItem, FavoriteShop
from favorites.schemas import FavoriteItemDTO, FavoriteShopDTO
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload


class FavoriteRepository(BaseRepository):

    async def add_item(self, item_id: int, user_id: int) -> FavoriteItem:
        async with self.get_session() as session:
            favorite = FavoriteItem(item_id=item_id, user_id=user_id)
            session.add(favorite)
            await session.commit()
            await session.refresh(favorite)
            return FavoriteItemDTO.model_validate(favorite)
    
    async def add_shop(self, shop_id: int, user_id: int) -> FavoriteShop:
        async with self.get_session() as session:
            favorite = FavoriteShop(shop_id=shop_id, user_id=user_id)
            session.add(favorite)
            await session.commit()
            await session.refresh(favorite)
            return FavoriteShopDTO.model_validate(favorite)

    async def get_favorite_items(
        self, user_id: int, limit: int = 10, 
        offset: int = 0, search: str | None = None
    ) -> tuple[list[FavoriteItemDTO], int]:
        async with self.get_session() as session:
            favorites = select(FavoriteItem).where(
                FavoriteItem.user_id == user_id
            )
            if search:
                favorites = favorites.options(
                    selectinload(FavoriteItem.item)
                ).where(
                    FavoriteItem.item.name.ilike(f"%{search}%")
                )
            favorites = favorites.limit(limit).offset(offset)
            favorites = await session.execute(favorites)
            favorites = favorites.scalars().all()
            
            count_query = select(func.count(FavoriteItem.id)).where(
                FavoriteItem.user_id == user_id
            )
            if search:
                count_query = count_query.options(
                    selectinload(FavoriteItem.item)
                ).where(
                    FavoriteItem.item.name.ilike(f"%{search}%")
                )
            count = await session.execute(count_query)
            count = count.scalar_one()
            return [
                FavoriteItemDTO.model_validate(favorite) for favorite in favorites
            ], count

    async def get_favorite_shops(
        self, user_id: int, limit: int = 10, 
        offset: int = 0, search: str | None = None
    ) -> tuple[list[FavoriteShopDTO], int]:
        async with self.get_session() as session:
            favorites = select(FavoriteShop).where(
                FavoriteShop.user_id == user_id
            )
            if search:
                favorites = favorites.options(
                    selectinload(FavoriteShop.shop)
                ).where(
                    FavoriteShop.shop.name.ilike(f"%{search}%")
                )
            favorites = favorites.limit(limit).offset(offset)
            favorites = await session.execute(favorites)
            favorites = favorites.scalars().all()
            
            count_query = select(func.count(FavoriteShop.id)).where(
                FavoriteShop.user_id == user_id
            )
            if search:
                count_query = count_query.options(
                    selectinload(FavoriteShop.shop)
                ).where(
                    FavoriteShop.shop.name.ilike(f"%{search}%")
                )   
            count = await session.execute(count_query)
            count = count.scalar_one()
            return [
                FavoriteShopDTO.model_validate(favorite) for favorite in favorites
            ], count
    
    async def remove_item(self, item_id: int, user_id: int) -> None:
        async with self.get_session() as session:
            await session.execute(
                delete(FavoriteItem).where(
                    FavoriteItem.item_id == item_id,
                    FavoriteItem.user_id == user_id
                )
            )
            await session.commit()

    async def remove_shop(self, shop_id: int, user_id: int) -> None:
        async with self.get_session() as session:
            await session.execute(
                delete(FavoriteShop).where(
                    FavoriteShop.shop_id == shop_id,
                    FavoriteShop.user_id == user_id
                )
            )
            await session.commit()
