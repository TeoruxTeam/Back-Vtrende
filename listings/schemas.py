from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from fastapi import Form
from pydantic import BaseModel, Field, HttpUrl, NonNegativeInt, model_validator

from core.schemas import CountSchema, StatusOkSchema


class PublishedSortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class LocationSchema(BaseModel):
    address: Optional[str]
    latitude: Decimal
    longitude: Decimal

    class Config:
        from_attributes = True


class GetListingsQuerySchema(BaseModel):
    limit: int = 10
    offset: int = 0
    search: Optional[str] = None
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    published_sort_order: Optional[PublishedSortOrder] = None


class CreateListingRequestSchema(BaseModel):
    title: str = Field(..., description="Title", max_length=100)
    description: str = Field(..., description="Description", max_length=5000)
    price: NonNegativeInt = Field(..., description="Price")
    video: Optional[HttpUrl] = Field(
        None, description="Link to the video", max_length=500
    )
    category_id: int = Field(
        ..., description="Category id, could be found in /categories"
    )
    subcategory_id: Optional[int] = Field(
        None,
        description="Subcategory id, could be found in /subcategories. If None - input 0",
    )
    latitude: Optional[Decimal] = Field(
        None, description="Latitude", ge=-90, le=90, max_digits=10, decimal_places=8
    )
    longitude: Optional[Decimal] = Field(
        None, description="Longitude", ge=-180, le=180, max_digits=11, decimal_places=8
    )

    @model_validator(mode="before")
    def check_location_fields(cls, values):
        latitude, longitude = values.get("latitude"), values.get("longitude")
        if latitude is None and longitude is not None:
            raise ValueError("error.location.latitude.missing")
        if longitude is None and latitude is not None:
            raise ValueError("error.location.longitude.missing")
        return values

    @model_validator(mode="before")
    def convert_subcategory_id(cls, values):
        """
        Convert subcategory_id=0 to None.
        """
        subcategory_id = values.get("subcategory_id")
        if subcategory_id == 0:
            values["subcategory_id"] = None
        return values

    @classmethod
    def as_form(
        cls,
        title: str = Form(..., description="Title", max_length=100),
        description: str = Form(..., description="Description", max_length=5000),
        video: Optional[HttpUrl] = Form(
            None, description="Link to the video", max_length=500
        ),
        price: int = Form(..., description="Price"),
        category_id: int = Form(
            ..., description="Category id, could be found in /categories"
        ),
        subcategory_id: int = Form(
            ...,
            description="Subcategory id, could be found in /subcategories. If None - input 0",
        ),
        latitude: Optional[Decimal] = Form(
            None,
            ge=-90,
            le=90,
            max_digits=10,
            decimal_places=8,
            description="Latitude, should be in range [-90, 90]",
        ),
        longitude: Optional[Decimal] = Form(
            None,
            ge=-180,
            le=180,
            max_digits=11,
            decimal_places=8,
            description="Longitude, should be in range [-180, 180]",
        ),
    ) -> "CreateListingRequestSchema":

        return cls(
            title=title,
            description=description,
            video=video,
            price=price,
            category_id=category_id,
            subcategory_id=subcategory_id,
            latitude=latitude,
            longitude=longitude,
        )


class UpdateListingRequestSchema(BaseModel):
    title: str = Field(..., description="Title", max_length=100)
    description: str = Field(..., description="Description", max_length=5000)
    video: Optional[HttpUrl] = Field(
        None, description="Link to the video", max_length=300
    )
    price: NonNegativeInt = Field(..., description="Price")
    category_id: int = Field(
        ..., description="Category id, could be found in /categories"
    )
    subcategory_id: Optional[int] = Field(
        None, description="Subcategory id, could be found in /subcategories"
    )
    latitude: Optional[Decimal] = Field(
        None, description="Latitude", ge=-90, le=90, max_digits=10, decimal_places=8
    )
    longitude: Optional[Decimal] = Field(
        None, description="Longitude", ge=-180, le=180, max_digits=11, decimal_places=8
    )
    remove_image_ids: List[int] = Field(
        [], description="List of image ids to remove from the listing"
    )
    remove_video: bool = Field(
        False, description="Flag to remove video from the listing"
    )

    @model_validator(mode="before")
    def check_location_fields(cls, values):
        latitude, longitude = values.get("latitude"), values.get("longitude")
        if latitude is None and longitude is not None:
            raise ValueError("error.location.latitude.missing")
        if longitude is None and latitude is not None:
            raise ValueError("error.location.longitude.missing")
        return values

    @classmethod
    def as_form(
        cls,
        title: str = Form(...),
        description: str = Form(...),
        video: Optional[HttpUrl] = Form(None),
        price: int = Form(...),
        category_id: int = Form(...),
        subcategory_id: Optional[int] = Form(None),
        latitude: Optional[Decimal] = Form(None),
        longitude: Optional[Decimal] = Form(None),
        remove_image_ids: List[int] = Form([]),
        remove_video: bool = Form(False),
    ) -> "CreateListingRequestSchema":
        return cls(
            title=title,
            description=description,
            video=video,
            price=price,
            category_id=category_id,
            subcategory_id=subcategory_id,
            latitude=latitude,
            longitude=longitude,
            remove_image_ids=remove_image_ids,
            remove_video=remove_video,
        )


class ImageSchema(BaseModel):
    id: int
    url: str

    class Config:
        from_attributes = True


class VideoSchema(BaseModel):
    id: int
    url: str

    class Config:
        from_attributes = True


class ListingDTO(BaseModel):
    id: int
    title: str
    description: str
    category_id: int
    subcategory_id: Optional[int] = None
    price: int
    user_id: int
    created_at: datetime
    moderation_status: str
    deleted_at: Optional[datetime] = None
    is_deleted: bool = False
    is_sold: bool = False
    sold_at: Optional[datetime] = None


class ListingAggregateDTO(ListingDTO):
    images: List[ImageSchema]
    video: Optional[VideoSchema]


class ListingSchema(BaseModel):
    id: int
    title: str
    description: str
    category_name: Optional[str] = None
    category_id: int
    subcategory_name: Optional[str] = None
    subcategory_id: Optional[int] = None
    price: int
    location: Optional[LocationSchema] = None
    images: List[ImageSchema]
    video: Optional[VideoSchema] = None
    user_id: int
    created_at: datetime
    moderation_status: str
    is_sold: bool
    sold_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class ListingWithPriority(ListingSchema):
    priority: int
class ListingWithFavoriteFlag(ListingSchema):
    is_favorite: bool

class ListingWithFavoriteFlagAndPriority(ListingWithFavoriteFlag):
    priority: int

class ShortListingSchema(BaseModel):
    id: int
    title: str
    price: int
    location: LocationSchema
    is_sold: bool
    sold_at: Optional[datetime]
    moderation_status: str
    created_at: datetime
    seller_id: int
    images: List[ImageSchema]


class ShortListingSchemaWithPriority(ShortListingSchema):
    priority: int


class ShortListingWithFavoriteFlag(ShortListingSchema):
    is_favorite: bool


class MyShortListingSchema(ShortListingSchema):
    reject_reason: Optional[str]


class AdminPShortListingSchema(ShortListingSchema):
    is_deleted: bool
    deleted_at: Optional[datetime]


class AdminDetailListingSchema(ListingSchema):
    is_deleted: bool
    deleted_at: Optional[datetime]


class GetListingResponseSchema(StatusOkSchema):
    data: ListingWithFavoriteFlagAndPriority


class CreateListingResponseSchema(StatusOkSchema):
    message: str = "success.listing.created"
    data: ListingSchema


class UpdateListingResponseSchema(StatusOkSchema):
    message: str = "success.listing.updated"
    data: ListingSchema


class ShortListingWithFavoriteFlagAndPriority(ShortListingWithFavoriteFlag):
    priority: int


class GetListingsResponseSchema(StatusOkSchema, CountSchema):
    data: List[ShortListingWithFavoriteFlagAndPriority]


class GetMyListingsResponseSchema(StatusOkSchema, CountSchema):
    data: List[MyShortListingSchema]


class GetUserListingsResponseSchema(StatusOkSchema, CountSchema):
    data: List[ShortListingWithFavoriteFlag]


class AddToFavoritesRequestSchema(BaseModel):
    listing_id: int


class RemoveFromFavoritesRequestSchema(BaseModel):
    listing_id: int


class AddToFavoritesResponseSchema(StatusOkSchema):
    message: str = "success.listing.added_to_favorites"


class RemoveFromFavoritesResponseSchema(StatusOkSchema):
    message: str = "success.listing.removed_from_favorites"


class GetMyFavoritesResponseSchema(StatusOkSchema, CountSchema):
    data: List[ShortListingWithFavoriteFlag]
