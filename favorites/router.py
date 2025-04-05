from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide
from core.container import Container
from users.schemas import UserDTO
from auth.depends import get_current_verified_buyer
from favorites.schemas import (
    AddItemToFavoritesResponseSchema,
    AddShopToFavoritesResponseSchema,
    GetFavoriteItemsResponseSchema,
    GetFavoriteShopsResponseSchema
)
from favorites.services import FavoriteService


router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.post("/item/{item_id}/")
@inject
async def add_item_to_favorites(
    item_id: int,
    current_user: UserDTO = Depends(get_current_verified_buyer),
    favorite_service: FavoriteService = Depends(Provide[Container.favorite_service]),
) -> AddItemToFavoritesResponseSchema:
    return await favorite_service.add_item_to_favorites(item_id, current_user.id)


@router.post("/shop/{shop_id}/")
@inject
async def add_shop_to_favorites(
    shop_id: int,
    current_user: UserDTO = Depends(get_current_verified_buyer),
    favorite_service: FavoriteService = Depends(Provide[Container.favorite_service]),
) -> AddShopToFavoritesResponseSchema:
    return await favorite_service.add_shop_to_favorites(shop_id, current_user.id)


@router.get("/items/", response_model=GetFavoriteItemsResponseSchema)
@inject
async def get_favorite_items(
    search: str | None = None,
    limit: int = 10,
    offset: int = 0,
    current_user: UserDTO = Depends(get_current_verified_buyer),
    favorite_service: FavoriteService = Depends(Provide[Container.favorite_service]),
) -> GetFavoriteItemsResponseSchema:
    return await favorite_service.get_favorite_items(
        current_user.id, limit, offset, search
    )

@router.get("/shops/", response_model=GetFavoriteShopsResponseSchema)
@inject
async def get_favorite_shops(
    search: str | None = None,
    limit: int = 10,
    offset: int = 0,
    current_user: UserDTO = Depends(get_current_verified_buyer),
    favorite_service: FavoriteService = Depends(Provide[Container.favorite_service]),
) -> GetFavoriteShopsResponseSchema:
    return await favorite_service.get_favorite_shops(
        current_user.id, limit, offset, search
    )

@router.delete("/item/{item_id}/")
@inject
async def remove_item_from_favorites(
    item_id: int,
    current_user: UserDTO = Depends(get_current_verified_buyer),
    favorite_service: FavoriteService = Depends(Provide[Container.favorite_service]),
) -> None:
    await favorite_service.remove_item_from_favorites(item_id, current_user.id)


@router.delete("/shop/{shop_id}/")
@inject
async def remove_shop_from_favorites(
    shop_id: int,
    current_user: UserDTO = Depends(get_current_verified_buyer),
    favorite_service: FavoriteService = Depends(Provide[Container.favorite_service]),
) -> None:
    await favorite_service.remove_shop_from_favorites(shop_id, current_user.id)

