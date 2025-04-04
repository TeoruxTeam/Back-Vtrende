from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from core.utils import get_media_url

from .repositories import IRatingRepository
from .schemas import RatingFromORM, RatingWithUserAndListingData, RatingWithUserData


class IRatingService(ABC):

    @abstractmethod
    async def create_rating(
        self, listing_id: int, comment: str, rating: int, user_id: int
    ) -> RatingFromORM:
        pass

    @abstractmethod
    async def get_user_avg_rating(self, user_id: int) -> float:
        pass

    @abstractmethod
    async def get_rating_by_listing_id(
        self, listing_id: int, user_id: int
    ) -> RatingFromORM:
        pass

    @abstractmethod
    async def edit_rating_by_listing_id(
        self, listing_id: int, comment: str, rating: int, user_id: int
    ) -> None:
        pass

    @abstractmethod
    async def delete_rating_by_listing_id(self, listing_id: int, user_id: int) -> None:
        pass

    @abstractmethod
    async def get_rating_for_listing_by_user_id(
        self, listing_id: int, user_id: int
    ) -> RatingFromORM:
        pass

    @abstractmethod
    async def verify_rating(self, rating_id: int) -> None:
        pass

    @abstractmethod
    async def get_reviews_by_seller_id(
        self, user_id: int, limit: int, offset: int, base_url: str
    ) -> Tuple[List[RatingWithUserAndListingData], int]:
        pass

    @abstractmethod
    async def get_rating(self, rating_id: int) -> Optional[RatingFromORM]:
        pass

    @abstractmethod
    async def get_nonverified_reviews(
        self, limit: int, offset: int
    ) -> Tuple[List[RatingFromORM], int]:
        pass

    @abstractmethod
    async def delete_rating_by_id(self, rating_id: int):
        pass

    @abstractmethod
    async def get_created_ratings_by_user_id(
        self, user_id: int, limit: int, offset: int
    ) -> Tuple[List[RatingFromORM], int]:
        pass

    @abstractmethod
    async def get_reviews_count(self, user_id: int) -> int:
        pass


class RatingService(IRatingService):

    def __init__(self, repo: IRatingRepository):
        self.repo = repo

    async def create_rating(
        self, listing_id: int, comment: str, rating: int, user_id: int
    ) -> RatingFromORM:
        return await self.repo.create_rating(listing_id, comment, rating, user_id)

    async def get_user_avg_rating(self, user_id: int) -> float:
        return await self.repo.get_user_avg_rating(user_id)

    async def get_rating_by_listing_id(
        self, listing_id: int, user_id: int
    ) -> RatingFromORM:
        return await self.repo.get_rating_by_listing_id(listing_id, user_id)

    async def edit_rating_by_listing_id(
        self, listing_id: int, comment: str, rating: int, user_id: int
    ) -> None:
        await self.repo.edit_rating_by_listing_id(listing_id, comment, rating, user_id)

    async def delete_rating_by_listing_id(self, listing_id: int, user_id: int) -> None:
        await self.repo.delete_rating_by_listing_id(listing_id, user_id)

    async def get_rating_for_listing_by_user_id(
        self, listing_id: int, user_id: int
    ) -> RatingFromORM:
        return await self.repo.get_rating_for_listing_by_user_id(listing_id, user_id)

    async def verify_rating(self, rating_id: int) -> None:
        await self.repo.verify_rating(rating_id)

    async def get_reviews_by_seller_id(
        self, user_id: int, limit: int, offset: int, base_url: str
    ) -> Tuple[List[RatingWithUserAndListingData], int]:
        reviews, count = await self.repo.get_reviews_by_seller_id(
            user_id, limit, offset
        )
        for review in reviews:
            review.avatar = get_media_url(base_url, review.avatar)
        for review in reviews:
            review.listing_image = get_media_url(base_url, review.listing_image)
        return reviews, count

    async def get_rating(self, rating_id: int) -> Optional[RatingFromORM]:
        return await self.repo.get_rating_by_id(rating_id)

    async def get_nonverified_reviews(
        self, limit: int, offset: int
    ) -> Tuple[List[RatingFromORM], int]:
        return await self.repo.get_nonverified_reviews(limit, offset)

    async def delete_rating_by_id(self, rating_id: int):
        await self.repo.delete_rating_by_id(rating_id)

    async def get_created_ratings_by_user_id(
        self, user_id: int, limit: int, offset: int
    ) -> Tuple[List[RatingFromORM], int]:
        return await self.repo.get_created_ratings_by_user_id(user_id, limit, offset)

    async def get_reviews_count(self, user_id: int) -> int:
        return await self.repo.get_reviews_count_by_user_id(user_id)
