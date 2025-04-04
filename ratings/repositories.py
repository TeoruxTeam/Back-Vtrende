from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from core.logger import logger
from core.repositories import BaseRepository
from listings.models import Listing, ListingImage

from .exceptions import RatingAlreadyExists
from .mappers import RatingMapper
from .models import Rating
from .schemas import RatingFromORM, RatingWithUserAndListingData, RatingWithUserData


class IRatingRepository(ABC):

    @abstractmethod
    async def create_rating(
        self, listing_id: int, comment: str, rating: int, user_id: int
    ) -> RatingFromORM:
        pass

    @abstractmethod
    async def get_user_avg_rating(self, user_id: int) -> float:
        pass

    @abstractmethod
    async def edit_rating_by_listing_id(
        self, listing_id: int, comment: str, rating: int, user_id: int
    ) -> None:
        pass

    @abstractmethod
    async def get_rating_by_listing_id(
        self, listing_id: int, user_id: int
    ) -> RatingFromORM:
        pass

    @abstractmethod
    async def delete_rating_by_listing_id(self, listing_id: int, user_id: int) -> None:
        pass

    @abstractmethod
    async def get_rating_for_listing_by_user_id(self, listing_id: int, user_id: int):
        pass

    @abstractmethod
    async def verify_rating(self, rating_id: int) -> None:
        pass

    @abstractmethod
    async def get_reviews_by_seller_id(
        self, user_id: int, limit: int, offset: int
    ) -> Tuple[List[RatingWithUserAndListingData], int]:
        pass

    @abstractmethod
    async def get_rating_by_id(self, rating_id: int) -> Optional[RatingFromORM]:
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
    async def get_reviews_count_by_user_id(self, user_id: int) -> int:
        pass


class RatingRepository(IRatingRepository, BaseRepository):

    async def create_rating(
        self, listing_id: int, comment: str, rating: int, user_id: int
    ) -> RatingFromORM:
        async with self.get_session() as session:
            try:
                rating = Rating(
                    listing_id=listing_id,
                    comment=comment,
                    rating=rating,
                    user_id=user_id,
                )
                session.add(rating)
                await session.commit()
                await session.refresh(rating)
                return RatingMapper.to_rating_from_orm(rating)
            except IntegrityError as e:
                await session.rollback()
                raise RatingAlreadyExists

    async def get_user_avg_rating(self, user_id: int) -> float:
        async with self.get_session() as session:
            result = await session.execute(
                select(func.avg(Rating.rating))
                .join(Listing, Rating.listing_id == Listing.id)
                .where(
                    Listing.user_id == user_id,
                    Rating.is_deleted == False,
                    Rating.verified == True,
                )
            )

            avg_rating = result.scalar()

            return avg_rating if avg_rating is not None else 0

    async def get_rating_by_listing_id(
        self, listing_id: int, user_id: int
    ) -> RatingFromORM:
        async with self.get_session() as session:
            result = await session.execute(
                select(Rating).where(
                    Rating.listing_id == listing_id,
                    Rating.user_id == user_id,
                    Rating.is_deleted == False,
                )
            )

            rating = result.scalar()
            return RatingMapper.to_rating_from_orm(rating) if rating else None

    async def edit_rating_by_listing_id(
        self, listing_id: int, comment: str, rating: int, user_id: int
    ) -> None:
        async with self.get_session() as session:
            await session.execute(
                update(Rating)
                .where(
                    Rating.listing_id == listing_id,
                    Rating.user_id == user_id,
                    Rating.is_deleted == False,
                )
                .values(comment=comment, rating=rating)
            )
            await session.commit()

    async def delete_rating_by_listing_id(self, listing_id: int, user_id: int) -> None:
        async with self.get_session() as session:
            await session.execute(
                update(Rating)
                .where(
                    Rating.listing_id == listing_id,
                    Rating.user_id == user_id,
                    Rating.is_deleted == False,
                )
                .values(is_deleted=True, deleted_at=datetime.now(timezone.utc))
            )
            await session.commit()

    async def get_rating_for_listing_by_user_id(
        self, listing_id: int, user_id: int
    ) -> RatingFromORM:
        async with self.get_session() as session:
            result = await session.execute(
                select(Rating).where(
                    Rating.listing_id == listing_id,
                    Rating.user_id == user_id,
                    Rating.is_deleted == False,
                )
            )

            rating = result.scalar()

            return RatingMapper.to_rating_from_orm(rating) if rating else None

    async def verify_rating(self, rating_id: int) -> None:
        async with self.get_session() as session:
            await session.execute(
                update(Rating)
                .where(Rating.id == rating_id, Rating.is_deleted == False)
                .values(verified=True)
            )
            await session.commit()

    async def get_reviews_by_seller_id(
        self, user_id: int, limit: int, offset: int
    ) -> Tuple[List[RatingWithUserAndListingData], int]:
        async with self.get_session() as session:
            logger.info(
                f"User id for reviews is {user_id}, limit {limit}, offset {offset}"
            )
            # Подзапрос для получения самой новой фотографии для каждого объявления
            latest_image_subquery = (
                select(ListingImage.listing_id, ListingImage.url)
                .where(ListingImage.is_deleted == False)
                .order_by(ListingImage.listing_id, ListingImage.created_at.desc())
                .distinct(ListingImage.listing_id)
                .subquery()
            )

            # Основной запрос с оптимизированными джоинами
            result = await session.execute(
                select(Rating, latest_image_subquery.c.url.label("listing_image"))
                .join(Listing, Rating.listing_id == Listing.id)
                .outerjoin(
                    latest_image_subquery,
                    Listing.id == latest_image_subquery.c.listing_id,
                )
                .where(
                    Listing.user_id == user_id,
                    Rating.is_deleted == False,
                    Rating.verified == True,
                )
                .options(
                    selectinload(Rating.user),  # Для загрузки данных пользователя
                    selectinload(
                        Rating.listing
                    ),  # Для загрузки связанных данных Listing
                )
                .limit(limit)
                .offset(offset)
            )

            rows = result.fetchall()
            logger.info(f"Rows {rows}")
            reviews = [
                RatingMapper.to_rating_with_user_and_listing_data_from_orm(
                    row[0], row.listing_image
                )
                for row in rows
            ]
            logger.info(f"Formatted ratings {reviews}")

            count_result = await session.execute(
                select(func.count(Rating.id))
                .join(Listing, Rating.listing_id == Listing.id)
                .where(
                    Listing.user_id == user_id,
                    Rating.is_deleted == False,
                    Rating.verified == True,
                )
            )
            count = count_result.scalar()
            logger.info(f"Count {count}")
            return reviews, count

    async def get_rating_by_id(self, rating_id: int) -> Optional[RatingFromORM]:
        async with self.get_session() as session:
            result = await session.execute(
                select(Rating).where(Rating.id == rating_id, Rating.is_deleted == False)
            )
            rating = result.scalar()
            if rating:
                return RatingMapper.to_rating_from_orm(rating)
            return None

    async def get_nonverified_reviews(
        self, limit: int, offset: int
    ) -> Tuple[List[RatingFromORM], int]:
        async with self.get_session() as session:
            result = await session.execute(
                select(Rating)
                .where(Rating.verified == False, Rating.is_deleted == False)
                .limit(limit)
                .offset(offset)
            )
            ratings = result.scalars().all()
            ratings = [RatingMapper.to_rating_from_orm(rating) for rating in ratings]

            count_result = await session.execute(
                select(func.count(Rating.id)).where(Rating.verified == False)
            )
            count = count_result.scalar()

            return ratings, count

    async def delete_rating_by_id(self, rating_id: int):
        async with self.get_session() as session:
            await session.execute(
                update(Rating)
                .where(Rating.id == rating_id)
                .values(is_deleted=True, deleted_at=datetime.now(timezone.utc))
            )
            await session.commit()

    async def get_created_ratings_by_user_id(
        self, user_id: int, limit: int, offset: int
    ) -> Tuple[List[RatingFromORM], int]:
        async with self.get_session() as session:
            result = await session.execute(
                select(Rating)
                .where(Rating.user_id == user_id, Rating.is_deleted == False)
                .limit(limit)
                .offset(offset)
            )
            ratings = result.scalars().all()
            ratings = [RatingMapper.to_rating_from_orm(rating) for rating in ratings]

            count_result = await session.execute(
                select(func.count(Rating.id)).where(
                    Rating.user_id == user_id, Rating.is_deleted == False
                )
            )
            count = count_result.scalar()

            return ratings, count

    async def get_reviews_count_by_user_id(self, user_id: int) -> int:
        async with self.get_session() as session:
            result = await session.execute(
                select(func.count(Rating.id))
                .join(Listing, Rating.listing_id == Listing.id)
                .where(Listing.user_id == user_id)
            )
            count = result.scalar()
            return count
