from typing import Optional

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, File, Request, UploadFile

from auth.depends import (
    get_current_verified_buyer,
    get_current_verified_seller_with_iin_bin,
    get_current_verified_seller,
    get_current_verified_seller_with_iin_bin,
    get_current_seller,
    get_current_verified_user
)
from core.container import Container


from .schemas import (
    GetMeResponseSchema,
    UserDTO,
    UpdateShop,
    UpdateShopResponseSchema,
    UpdateShopImageResponseSchema
)
from .services import UserService

router = APIRouter(
    prefix="/profile",
    tags=["profile"],
)


@router.get("/me/", response_model=GetMeResponseSchema)
@inject
async def get_me(
    user_service: UserService = Depends(Provide[Container.user_service]),
    user: UserDTO = Depends(get_current_verified_user),
):
    return await user_service.get_me(user)


@router.patch("/shop/", response_model=UpdateShopResponseSchema)
@inject
async def update_me(
    payload: UpdateShop,
    user_service: UserService = Depends(Provide[Container.user_service]),
    user: UserDTO = Depends(get_current_verified_seller_with_iin_bin),
):
    return await user_service.update_shop(user, payload)


@router.patch("/shop/photo/", response_model=UpdateShopImageResponseSchema)
@inject
async def update_shop_photo(
    photo: UploadFile = File(...),
    user_service: UserService = Depends(Provide[Container.user_service]),
    user: UserDTO = Depends(get_current_verified_seller_with_iin_bin),
):
    return await user_service.update_shop_photo(user, photo)