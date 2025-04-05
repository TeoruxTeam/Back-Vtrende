from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, File, Query, Request, UploadFile

from auth.depends import (
    get_current_user,
    get_current_seller,
    get_current_verified_seller,
    get_current_verified_seller_with_iin_bin,
    get_current_verified_buyer,
    get_current_verified_user
)
from users.schemas import UserDTO
from items.services import ItemService
from core.container import Container
from items.schemas import (
    CreateItem,
    UpdateItem,
    GetMyItemsResponseSchema,
    GetMyItemResponseSchema,
    CreateItemResponseSchema,
    UpdateItemResponseSchema,
    GetItemsResponseSchema,
    GetCatalogResponseSchema,
    GetItemResponseSchema
)


router = APIRouter(
    prefix="/shop",
    tags=["shop"],
)


@router.get("/self/")
@inject
async def get_my_items(
    search: str | None = None,
    limit: int = 10,
    offset: int = 0,
    current_user: UserDTO = Depends(get_current_verified_seller_with_iin_bin),
    item_service: ItemService = Depends(Provide[Container.item_service]),
) -> GetMyItemsResponseSchema:
    return await item_service.get_my_items(
        current_user, search, limit, offset
    )


@router.get("/self/{item_id}/")
async def get_my_item(
    item_id: int,
    current_user: UserDTO = Depends(get_current_verified_seller_with_iin_bin),
    item_service: ItemService = Depends(Provide[Container.item_service]),
) -> GetMyItemResponseSchema:
    return await item_service.get_my_item(item_id, current_user)


@router.post("/item/")
async def create_item(
    item: CreateItem,
    current_user: UserDTO = Depends(get_current_verified_seller_with_iin_bin),
    item_service: ItemService = Depends(Provide[Container.item_service]),
) -> CreateItemResponseSchema:
    return await item_service.create_item(item, current_user)


@router.patch("/self/{item_id}/")
async def update_item(
    item_id: int,
    item: UpdateItem,
    current_user: UserDTO = Depends(get_current_verified_seller_with_iin_bin),
    item_service: ItemService = Depends(Provide[Container.item_service]),
) -> UpdateItemResponseSchema:
    return await item_service.update_item(item_id, item, current_user)


@router.delete("/self/{item_id}/")
async def delete_item(
    item_id: int,
    current_user: UserDTO = Depends(get_current_verified_seller_with_iin_bin),
    item_service: ItemService = Depends(Provide[Container.item_service]),
):
    await item_service.delete_item(item_id, current_user)


@router.get("/{shop_id}/")
async def get_shop_items(
    shop_id: int,
    search: str | None = None,
    limit: int = 10,
    offset: int = 0,
    current_user: UserDTO = Depends(get_current_verified_user),
    item_service: ItemService = Depends(Provide[Container.item_service]),
) -> GetItemsResponseSchema:
    return await item_service.get_shop_items(shop_id, search, limit, offset)


@router.get("/catalog/")
async def get_catalog(
    search: str | None = None,
    limit: int = 10,
    offset: int = 0,
    item_service: ItemService = Depends(Provide[Container.item_service]),
    user: UserDTO = Depends(get_current_verified_user),
) -> GetCatalogResponseSchema:
    return await item_service.get_catalog(search, limit, offset)


@router.get("/{item_id}/")
async def get_item(
    item_id: int,
    current_user: UserDTO = Depends(get_current_verified_user),
    item_service: ItemService = Depends(Provide[Container.item_service]),
) -> GetItemResponseSchema:
    return await item_service.get_item(item_id)