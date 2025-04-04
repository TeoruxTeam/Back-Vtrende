from decimal import Decimal
from typing import List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, File, Path, Query, Request, UploadFile

from auth.depends import get_current_confirmed_user, get_current_confirmed_user_optional
from chats.facade import IChatFacade
from chats.schemas import GetListingChatResponseSchema
from core.container import Container
from core.logger import logger
from core.utils import get_language_from_cookies
from ratings.facade import IRatingFacade
from ratings.schemas import (
    GetMyRatingResponseSchema,
    GetUserRatingResponseSchema,
    RateListingRequestSchema,
    RateListingResponseSchema,
    UpdateRatingRequestSchema,
    UpdateRatingResponseSchema,
    VerifyRatingResponseSchema,
)
from recommendations.facade import IRecommendationFacade
from users.schemas import UserDTO

from .facade import IListingFacade
from .schemas import (
    AddToFavoritesRequestSchema,
    AddToFavoritesResponseSchema,
    CreateListingRequestSchema,
    CreateListingResponseSchema,
    GetListingResponseSchema,
    GetListingsQuerySchema,
    GetListingsResponseSchema,
    GetMyFavoritesResponseSchema,
    PublishedSortOrder,
    RemoveFromFavoritesRequestSchema,
    RemoveFromFavoritesResponseSchema,
    UpdateListingRequestSchema,
    UpdateListingResponseSchema,
)

router = APIRouter(
    prefix="/listings",
    tags=["/listings"],
)


@router.post("/", response_model=CreateListingResponseSchema)
@inject
async def create_listing(
    request: Request,
    language: str = Depends(get_language_from_cookies),
    form_data: CreateListingRequestSchema = Depends(CreateListingRequestSchema.as_form),
    images: List[UploadFile] = File(..., description="1-5 images"),
    current_user: UserDTO = Depends(get_current_confirmed_user),
    listing_facade: IListingFacade = Depends(Provide[Container.listing_facade]),
):
    """Create a new listing EP."""
    return await listing_facade.create_listing(
        form_data, images, current_user, request.base_url, language
    )


@router.put("/{listing_id:int}/", response_model=UpdateListingResponseSchema)
@inject
async def update_listing(
    request: Request,
    listing_id: int,
    language: str = Depends(get_language_from_cookies),
    form_data: UpdateListingRequestSchema = Depends(UpdateListingRequestSchema.as_form),
    images: List[UploadFile] = File(None, description="0-5 images"),
    current_user: UserDTO = Depends(get_current_confirmed_user),
    listing_facade: IListingFacade = Depends(Provide[Container.listing_facade]),
):
    """Update an existing listing EP."""
    return await listing_facade.update_listing(
        listing_id, form_data, images, current_user, request.base_url, language
    )


@router.delete("/{listing_id:int}/")
@inject
async def delete_listing(
    listing_id: int,
    current_user: UserDTO = Depends(get_current_confirmed_user),
    listing_facade: IListingFacade = Depends(Provide[Container.listing_facade]),
):
    """Delete an existing listing EP."""
    return await listing_facade.delete_listing(listing_id, current_user)


@router.get("/{listing_id:int}/", response_model=GetListingResponseSchema)
@inject
async def get_listing_by_id(
    request: Request,
    listing_id: int,
    language: str = Depends(get_language_from_cookies),
    current_user: Optional[UserDTO] = Depends(get_current_confirmed_user_optional),
    recommendation_facade: IRecommendationFacade = Depends(
        Provide[Container.recommendation_facade]
    ),
    listing_facade: IListingFacade = Depends(Provide[Container.listing_facade]),
):
    """Get a listing by ID EP. If the listing is not moderated, only the owner can see it."""
    response: GetListingResponseSchema = await listing_facade.get_listing_by_id(
        listing_id, current_user, request.base_url, language
    )
    if current_user:
        await recommendation_facade.add_user_interest_statistics(
            current_user.id, response.data.category_id, response.data.subcategory_id
        )
    return response


@router.get("/", response_model=GetListingsResponseSchema)
@inject
async def get_listings(
    request: Request,
    limit: int = Query(10, description="Number of listings to return"),
    offset: int = Query(0, description="Number of listings to skip"),
    search: Optional[str] = Query(None, description="Search term for listings"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    subcategory_id: Optional[int] = Query(None, description="Filter by subcategory ID"),
    latitude: Optional[Decimal] = Query(
        None,
        description="Filter by latitude",
        ge=Decimal("-90.00000000"),
        le=Decimal("90.00000000"),
    ),
    longitude: Optional[Decimal] = Query(
        None,
        description="Filter by longitude",
        ge=Decimal("-180.00000000"),
        le=Decimal("180.00000000"),
    ),
    price_min: Optional[int] = Query(None, description="Filter by minimum price"),
    price_max: Optional[int] = Query(None, description="Filter by maximum price"),
    published_sort_order: PublishedSortOrder = Query(
        None,
        description="Sort by date: 'asc' for oldest first, 'desc' for newest first",
    ),
    current_user: Optional[UserDTO] = Depends(get_current_confirmed_user_optional),
    recommendation_facade: IRecommendationFacade = Depends(
        Provide[Container.recommendation_facade]
    ),
    listing_facade: IListingFacade = Depends(Provide[Container.listing_facade]),
):
    """Get a list of moderated listings EP."""
    queries = GetListingsQuerySchema(
        limit=limit,
        offset=offset,
        search=search,
        category_id=category_id,
        subcategory_id=subcategory_id,
        latitude=latitude,
        longitude=longitude,
        price_min=price_min,
        price_max=price_max,
        published_sort_order=published_sort_order,
    )
    if current_user:
        await recommendation_facade.add_user_interest_statistics(
            current_user.id, queries.category_id, queries.subcategory_id
        )
    return await listing_facade.get_listings(queries, request.base_url, current_user)


@router.post("/favorites/", response_model=AddToFavoritesResponseSchema)
@inject
async def add_to_favorites(
    schema: AddToFavoritesRequestSchema,
    current_user: UserDTO = Depends(get_current_confirmed_user),
    listing_facade: IListingFacade = Depends(Provide[Container.listing_facade]),
):
    """Add a listing to favorites EP."""
    return await listing_facade.add_to_favorites(schema, current_user)


@router.delete("/favorites/", response_model=RemoveFromFavoritesResponseSchema)
@inject
async def remove_from_favorites(
    schema: RemoveFromFavoritesRequestSchema,
    current_user: UserDTO = Depends(get_current_confirmed_user),
    listing_facade: IListingFacade = Depends(Provide[Container.listing_facade]),
):
    """Remove a listing from favorites EP."""
    return await listing_facade.remove_from_favorites(schema, current_user)


@router.get("/favorites/", response_model=GetMyFavoritesResponseSchema)
@inject
async def get_favorites(
    request: Request,
    limit: int = Query(10, description="Number of listings to return"),
    offset: int = Query(0, description="Number of listings to skip"),
    current_user: UserDTO = Depends(get_current_confirmed_user),
    listing_facade: IListingFacade = Depends(Provide[Container.listing_facade]),
):
    """Get a list of favorite listings EP."""
    return await listing_facade.get_favorites(
        current_user, limit, offset, request.base_url
    )


@router.get("/{listing_id:int}/chat/", response_model=GetListingChatResponseSchema)
@inject
async def get_listing_chat(
    listing_id: int,
    current_user: UserDTO = Depends(get_current_confirmed_user),
    chat_facade: IChatFacade = Depends(Provide[Container.chat_facade]),
):
    """Get a short chat info for a listing EP."""
    return await chat_facade.get_short_listing_chat_as_buyer(
        listing_id, current_user.id
    )


@router.post("/{listing_id:int}/rate/", response_model=RateListingResponseSchema)
@inject
async def rate_listing(
    listing_id: int,
    schema: RateListingRequestSchema,
    current_user: UserDTO = Depends(get_current_confirmed_user),
    rating_facade: IRatingFacade = Depends(Provide[Container.rating_facade]),
):
    """Rate a listing"""
    return await rating_facade.rate(listing_id, schema, current_user)


@router.get("/{listing_id:int}/my-rating/", response_model=GetMyRatingResponseSchema)
@inject
async def get_my_rating_for_listing(
    listing_id: int,
    current_user: UserDTO = Depends(get_current_confirmed_user),
    rating_facade: IRatingFacade = Depends(Provide[Container.rating_facade]),
):
    """Get my rating for a listing"""
    return await rating_facade.get_my_rating_for_listing(listing_id, current_user)


@router.put("/{listing_id:int}/my-rating/", response_model=RateListingResponseSchema)
@inject
async def update_my_rating_for_listing(
    listing_id: int,
    schema: UpdateRatingRequestSchema,
    current_user: UserDTO = Depends(get_current_confirmed_user),
    rating_facade: IRatingFacade = Depends(Provide[Container.rating_facade]),
):
    """Update my rating for a listing"""
    return await rating_facade.update_my_rating_by_listing_id(
        listing_id, schema, current_user
    )


@router.delete("/{listing_id:int}/my-rating/", response_model=None)
@inject
async def delete_my_rating_for_listing(
    listing_id: int,
    current_user: UserDTO = Depends(get_current_confirmed_user),
    rating_facade: IRatingFacade = Depends(Provide[Container.rating_facade]),
):
    """Delete my rating for a listing"""
    return await rating_facade.delete_my_rating_by_listing_id(
        listing_id, current_user.id
    )
