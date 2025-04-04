from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from core.schemas import CountSchema, StatusOkSchema


class RatingFromORM(BaseModel):
    id: int
    listing_id: int
    comment: str
    rating: int
    user_id: int
    verified: bool
    created_at: datetime


class RatingWithUserData(RatingFromORM):
    avatar: Optional[str]
    username: str


class RatingWithUserAndListingData(RatingWithUserData):
    listing_title: str
    listing_price: float
    listing_image: Optional[str]


class AvgRatingFloat(BaseModel):
    rating: float


class RateListingRequestSchema(BaseModel):
    comment: str
    rating: int = Field(..., ge=1, le=5)


class UpdateRatingRequestSchema(BaseModel):
    comment: str
    rating: int = Field(..., ge=1, le=5)


class GetUserRatingResponseSchema(StatusOkSchema):
    data: AvgRatingFloat


class GetMyRatingResponseSchema(StatusOkSchema):
    data: RatingFromORM


class RateListingResponseSchema(StatusOkSchema):
    message: str = "success.listing.rating.created"
    data: RatingFromORM


class UpdateRatingResponseSchema(StatusOkSchema):
    message: str = "success.listing.rating.updated"
    data: RatingFromORM


class VerifyRatingResponseSchema(StatusOkSchema):
    message: str = "success.listing.rating.verified"
    data: RatingFromORM


class GetRatingApplicationsResponseSchema(StatusOkSchema, CountSchema):
    data: List[RatingFromORM]


class GetUserReviewsResponseSchema(StatusOkSchema, CountSchema):
    data: List[RatingWithUserAndListingData]


class GetUserRatingsResponseSchema(StatusOkSchema, CountSchema):
    data: List[RatingFromORM]
