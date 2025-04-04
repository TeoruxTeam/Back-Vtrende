from abc import ABC, abstractmethod

from listings.exceptions import ListingNotFound
from listings.services import IListingService
from users.schemas import UserDTO

from .exceptions import CantRateYourself, RatingNotFound
from .schemas import (
    GetMyRatingResponseSchema,
    GetRatingApplicationsResponseSchema,
    GetUserRatingResponseSchema,
    GetUserRatingsResponseSchema,
    GetUserReviewsResponseSchema,
    RateListingRequestSchema,
    RateListingResponseSchema,
    UpdateRatingRequestSchema,
    UpdateRatingResponseSchema,
    VerifyRatingResponseSchema,
)
from .services import IRatingService


class IRatingFacade(ABC):

    @abstractmethod
    async def rate(
        self, listing_id: int, schema: RateListingRequestSchema, current_user: UserDTO
    ) -> RateListingResponseSchema:
        pass

    @abstractmethod
    async def get_user_rating(self, user_id: int) -> GetUserRatingResponseSchema:
        pass

    @abstractmethod
    async def get_my_rating_for_listing(
        self, listing_id: int, current_user: UserDTO
    ) -> GetMyRatingResponseSchema:
        pass

    @abstractmethod
    async def update_my_rating_by_listing_id(
        self, listing_id: int, schema: UpdateRatingRequestSchema, user: UserDTO
    ) -> UpdateRatingResponseSchema:
        pass

    @abstractmethod
    async def delete_my_rating_by_listing_id(
        self, listing_id: int, user_id: int
    ) -> None:
        pass

    @abstractmethod
    async def verify_rating(self, rating_id: int) -> VerifyRatingResponseSchema:
        pass

    @abstractmethod
    async def get_reviews_by_seller_id(
        self, user_id: int, limit: int, offset: int, base_url: str
    ) -> GetUserReviewsResponseSchema:
        pass

    @abstractmethod
    async def get_rating_applications(
        self, limit: int, offset: int
    ) -> GetRatingApplicationsResponseSchema:
        pass

    @abstractmethod
    async def delete_rating_by_id(self, rating_id: int):
        pass

    @abstractmethod
    async def get_created_ratings_by_user_id(
        self, user_id: int, limit: int, offset: int
    ) -> GetUserRatingsResponseSchema:
        pass


class RatingFacade(IRatingFacade):

    def __init__(
        self, rating_service: IRatingService, listing_service: IListingService
    ):
        self.rating_service = rating_service
        self.listing_service = listing_service

    async def rate(
        self, listing_id: int, schema: RateListingRequestSchema, current_user: UserDTO
    ) -> RateListingResponseSchema:
        listing = await self.listing_service.get_listing_by_id(listing_id)
        if not listing:
            raise ListingNotFound()
        if listing.user_id == current_user.id:
            raise CantRateYourself()
        rating = await self.rating_service.create_rating(
            listing_id, schema.comment, schema.rating, current_user.id
        )
        return RateListingResponseSchema(data=rating)

    async def update_my_rating_by_listing_id(
        self, listing_id: int, schema: UpdateRatingRequestSchema, user: UserDTO
    ) -> UpdateRatingResponseSchema:
        await self.rating_service.edit_rating_by_listing_id(
            listing_id, schema.comment, schema.rating, user.id
        )
        rating = await self.rating_service.get_rating_by_listing_id(listing_id, user.id)
        if rating:
            return UpdateRatingResponseSchema(data=rating)
        else:
            raise RatingNotFound()

    async def get_user_rating(self, user_id: int) -> GetUserRatingResponseSchema:
        rating = await self.rating_service.get_user_avg_rating(user_id)
        return GetUserRatingResponseSchema(data={"rating": rating})

    async def get_my_rating_for_listing(
        self, listing_id: int, current_user: UserDTO
    ) -> GetMyRatingResponseSchema:
        rating = await self.rating_service.get_rating_for_listing_by_user_id(
            listing_id, current_user.id
        )
        if not rating:
            raise RatingNotFound()
        return GetMyRatingResponseSchema(data=rating)

    async def delete_my_rating_by_listing_id(
        self, listing_id: int, user_id: int
    ) -> None:
        await self.rating_service.delete_rating_by_listing_id(listing_id, user_id)

    async def verify_rating(self, rating_id: int) -> VerifyRatingResponseSchema:
        await self.rating_service.verify_rating(rating_id)
        rating = await self.rating_service.get_rating(rating_id)
        return VerifyRatingResponseSchema(data=rating)

    async def get_reviews_by_seller_id(
        self, user_id: int, limit: int, offset: int, base_url: str
    ) -> GetUserReviewsResponseSchema:
        reviews, count = await self.rating_service.get_reviews_by_seller_id(
            user_id, limit, offset, base_url
        )
        return GetUserReviewsResponseSchema(count=count, data=reviews)

    async def get_rating_applications(
        self, limit: int, offset: int
    ) -> GetRatingApplicationsResponseSchema:
        reviews, count = await self.rating_service.get_nonverified_reviews(
            limit, offset
        )
        return GetRatingApplicationsResponseSchema(count=count, data=reviews)

    async def delete_rating_by_id(self, rating_id: int):
        await self.rating_service.delete_rating_by_id(rating_id)

    async def get_created_ratings_by_user_id(
        self, user_id: int, limit: int, offset: int
    ) -> GetUserRatingsResponseSchema:
        reviews, count = await self.rating_service.get_created_ratings_by_user_id(
            user_id, limit, offset
        )
        return GetUserRatingsResponseSchema(count=count, data=reviews)
