from pydantic import BaseModel, ConfigDict
from core.schemas import StatusOkSchema, CountSchema
from datetime import datetime


class FavoriteItemDTO(BaseModel):
    id: int
    item_id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FavoriteShopDTO(BaseModel):
    id: int
    shop_id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AddItemToFavoritesResponseSchema(StatusOkSchema):
    data: FavoriteItemDTO
    message: str = "success.favorites.item.added"

class AddShopToFavoritesResponseSchema(StatusOkSchema):
    data: FavoriteShopDTO
    message: str = "success.favorites.shop.added"

class GetFavoriteItemsResponseSchema(StatusOkSchema, CountSchema):   
    data: list[FavoriteItemDTO]

class GetFavoriteShopsResponseSchema(StatusOkSchema, CountSchema):   
    data: list[FavoriteShopDTO]



