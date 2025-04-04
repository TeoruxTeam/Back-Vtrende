from typing import Optional

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, File, Path, Query, Request, UploadFile

from auth.depends import get_current_confirmed_user, get_current_confirmed_user_optional
from chats.facade import IChatFacade
from chats.schemas import GetChatListResponseSchema
from core.container import Container
from items.facade import IListingFacade
from items.schemas import GetMyListingsResponseSchema, GetUserListingsResponseSchema
from ratings.facade import IRatingFacade
from ratings.schemas import GetUserRatingResponseSchema, GetUserReviewsResponseSchema

from .facade import IUserFacade
from .schemas import (
    GetMeResponseSchema,
    GetSellerInfoResponseSchema,
    PatchPasswordRequestSchema,
    PatchPasswordResponseSchema,
    PutMeRequestSchema,
    PutMeResponseSchema,
    UserDTO,
)
from .services import IUserService

router = APIRouter(
    prefix="/profile",
    tags=["profile"],
)


@router.get("/{user_id:int}/seller-info/", response_model=GetSellerInfoResponseSchema)
@inject
async def get_seller_info(
    user_id: int,
    request: Request,
    user_facade: IUserFacade = Depends(Provide[Container.user_facade]),
):
    return await user_facade.get_seller_info(user_id, request.base_url)


@router.get("/me/", response_model=GetMeResponseSchema)
@inject
async def get_me(
    request: Request,
    user_service: IUserService = Depends(Provide[Container.user_service]),
    user: UserDTO = Depends(get_current_confirmed_user),
):
    return await user_service.get_me(user, request.base_url)


@router.put("/me/", response_model=PutMeResponseSchema)
@inject
async def put_me(
    request: Request,
    payload: PutMeRequestSchema = Depends(PutMeRequestSchema.as_form),
    user_service: IUserService = Depends(Provide[Container.user_service]),
    photo: Optional[UploadFile] = File(
        None, description="User photo. If selected, it will replace the current one."
    ),
    user: UserDTO = Depends(get_current_confirmed_user),
):
    return await user_service.put_me(payload, photo, user, request.base_url)


@router.patch("/me/password/", response_model=PatchPasswordResponseSchema)
@inject
async def patch_password(
    payload: PatchPasswordRequestSchema,
    user_service: IUserService = Depends(Provide[Container.user_service]),
    user: UserDTO = Depends(get_current_confirmed_user),
):
    return await user_service.patch_password(payload, user)


@router.get("/me/listings/", response_model=GetMyListingsResponseSchema)
@inject
async def get_my_listings(
    request: Request,
    limit: int = Query(10, description="Limit of listings to return"),
    offset: int = Query(0, description="Offset of listings"),
    listing_facade: IListingFacade = Depends(Provide[Container.listing_facade]),
    user: UserDTO = Depends(get_current_confirmed_user),
):
    return await listing_facade.get_my_listings(user, limit, offset, request.base_url)


@router.get("/me/chats", response_model=GetChatListResponseSchema)
@inject
async def get_user_chats(
    request: Request,
    limit: int = Query(10, description="Limit of chats to return"),
    offset: int = Query(0, description="Offset of chats"),
    current_user: UserDTO = Depends(get_current_confirmed_user),
    chat_facade: IChatFacade = Depends(Provide[Container.chat_facade]),
):
    return await chat_facade.get_user_chats(
        current_user.id, limit, offset, request.base_url
    )


@router.get("/{user_id}/listings/", response_model=GetUserListingsResponseSchema)
@inject
async def get_user_listings(
    request: Request,
    user_id: int = Path(..., description="User ID"),
    user: Optional[UserDTO] = Depends(get_current_confirmed_user_optional),
    limit: int = Query(10, description="Limit of listings to return"),
    offset: int = Query(0, description="Offset of listings"),
    listing_facade: IListingFacade = Depends(Provide[Container.listing_facade]),
):
    return await listing_facade.get_user_listings(
        user_id, limit, offset, request.base_url, user
    )


@router.get("/{user_id}/rating/", response_model=GetUserRatingResponseSchema)
@inject
async def get_user_rating(
    user_id: int,
    rating_facade: IRatingFacade = Depends(Provide[Container.rating_facade]),
):
    return await rating_facade.get_user_rating(user_id)


@router.get("/{user_id}/reviews/", response_model=GetUserReviewsResponseSchema)
@inject
async def get_user_reviews(
    user_id: int,
    request: Request,
    limit: int = Query(10, description="Number of reviews to return"),
    offset: int = Query(0, description="Number of reviews to skip"),
    rating_facade: IRatingFacade = Depends(Provide[Container.rating_facade]),
):
    return await rating_facade.get_reviews_by_seller_id(
        user_id, limit, offset, request.base_url
    )
