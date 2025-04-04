from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from admin.schemas import ModerationApplication, RejectApplicationRequest
from core.logger import logger
from core.repositories import BaseRepository
from core.utils import get_media_url

from .exceptions import ListingIsAlreadyFavorite
from .repositories import (
    IFavoriteListingRepository,
    IListingAggregateRepository,
    IListingRepository,
)
from .schemas import (
    AdminPShortListingSchema,
    CreateListingRequestSchema,
    GetListingResponseSchema,
    GetListingsQuerySchema,
    ImageSchema,
    ListingAggregateDTO,
    ListingDTO,
    ListingSchema,
    ListingWithFavoriteFlag,
    ShortListingSchema,
    ShortListingSchemaWithPriority,
    UpdateListingRequestSchema,
    UpdateListingResponseSchema,
    ListingWithPriority
)


class IListingAggregateService(ABC):
    @abstractmethod
    async def create_listing_aggregate(
        self,
        form_data: CreateListingRequestSchema,
        location_id: int,
        images: List[UploadFile],
        user_id: int,
        session: AsyncSession,
    ) -> ListingAggregateDTO:
        pass

    @abstractmethod
    async def update_listing_aggregate(
        self,
        listing_id: int,
        form_data: UpdateListingRequestSchema,
        location_id: int,
        images: List[UploadFile],
        session: AsyncSession,
    ) -> UpdateListingResponseSchema:
        pass

    @abstractmethod
    async def get_active_listings(
        self, query: GetListingsQuerySchema
    ) -> Tuple[List[ShortListingSchemaWithPriority], int]:
        pass

    @abstractmethod
    async def get_unmoderated_listings(
        self, limit: int, offset: int, base_url: str
    ) -> Tuple[List[ModerationApplication], int]:
        pass

    @abstractmethod
    async def get_unmoderated_listing_by_id(
        self, listing_id: int, base_url: str
    ) -> ModerationApplication:
        pass

    @abstractmethod
    async def get_all_listings(
        self, limit: int, offset: int
    ) -> Tuple[List[ShortListingSchema], int]:
        pass

    @abstractmethod
    async def get_listing_by_id(self, listing_id: int) -> ListingWithPriority:
        pass

    @abstractmethod
    async def delete_listing_aggregate(
        self, listing_id: int, session: AsyncSession
    ) -> None:
        pass

    @abstractmethod
    async def get_listing_images(self, listing_id: int) -> List[ImageSchema]:
        pass

    @abstractmethod
    async def get_listings_by_user_id(
        self, user_id: int, owner: bool, admin: bool, limit: int, offset: int
    ) -> List[ShortListingSchema | AdminPShortListingSchema]:
        pass

    @abstractmethod
    async def get_favorite_listings(
        self, user_id: int, limit: int, offset: int
    ) -> Tuple[List[ShortListingSchema], int]:
        pass


class IListingService(ABC):
    @abstractmethod
    async def get_approved_listing_by_id(self, listing_id: int) -> Optional[ListingDTO]:
        pass

    @abstractmethod
    async def get_listing_by_id(self, listing_id: int) -> ListingWithFavoriteFlag:
        pass

    @abstractmethod
    async def reject_listing(
        self, listing_id: int, schema: RejectApplicationRequest
    ) -> None:
        pass

    @abstractmethod
    async def approve_listing(self, listing_id: int) -> None:
        pass

    @abstractmethod
    async def get_total_active_listings_count(self) -> int:
        pass

    @abstractmethod
    async def get_active_listings_month_count(self) -> int:
        pass

    @abstractmethod
    async def get_refused_listings_count(self) -> int:
        pass


class IFavoriteListingService(ABC):
    @abstractmethod
    async def add_favorite(self, listing_id: int, user_id: int) -> None:
        pass

    @abstractmethod
    async def remove_favorite(self, listing_id: int, user_id: int) -> None:
        pass

    @abstractmethod
    async def get_user_favorite_listing_ids(
        self, user_id: int, listing_ids: List[int]
    ) -> List[int]:
        pass

    @abstractmethod
    async def is_favorite(self, listing_id: int, user_id: int) -> bool:
        pass


class ListingAggregateService(IListingAggregateService):
    def __init__(
        self,
        repo: IListingAggregateRepository,
    ):
        self.repo = repo

    async def create_listing_aggregate(
        self,
        form_data: CreateListingRequestSchema,
        location_id: int,
        images: List[UploadFile],
        user_id: int,
        session: AsyncSession,
    ) -> ListingAggregateDTO:
        logger.warning(f"ListingAggregateService")
        return await self.repo.create_listing_aggregate(
            form_data, location_id, images, user_id, session
        )

    async def get_active_listings(
        self, query: GetListingsQuerySchema
    ) -> Tuple[List[ShortListingSchemaWithPriority], int]:
        return await self.repo.get_active_listings(query)

    async def get_all_listings(
        self, limit: int, offset: int
    ) -> Tuple[List[ShortListingSchema], int]:
        return await self.repo.get_all_listings(limit, offset)

    async def get_unmoderated_listings(
        self, limit: int, offset: int, base_url: str
    ) -> Tuple[List[ModerationApplication], int]:
        listings, count = await self.repo.get_unmoderated_listings(limit, offset)
        for listing in listings:
            for image in listing.images:
                image.url = get_media_url(base_url, image.url)
        return listings, count

    async def get_unmoderated_listing_by_id(
        self, listing_id: int, base_url: str
    ) -> ModerationApplication:
        listing = await self.repo.get_unmoderated_listing_by_id(listing_id)
        if not listing:
            return None

        for image in listing.images:
            image.url = get_media_url(base_url, image.url)
        return listing

    async def update_listing_aggregate(
        self,
        listing_id: int,
        form_data: UpdateListingRequestSchema,
        location_id: int,
        images: List[UploadFile],
        session: AsyncSession,
    ) -> UpdateListingResponseSchema:
        return await self.repo.update_listing_aggregate(
            listing_id, form_data, location_id, images, session
        )

    async def get_listing_by_id(self, listing_id: int) -> ListingWithPriority:
        return await self.repo.get_listing_by_id(listing_id)

    async def delete_listing_aggregate(
        self, listing_id: int, session: AsyncSession
    ) -> None:
        time_now = datetime.now(timezone.utc)
        return await self.repo.delete_listing_aggregate(listing_id, time_now, session)

    async def get_listing_images(self, listing_id: int) -> List[ImageSchema]:
        return await self.repo.get_listing_images(listing_id)

    async def get_listings_by_user_id(
        self, user_id: int, owner: bool, admin: bool, limit: int, offset: int
    ) -> List[ShortListingSchema | AdminPShortListingSchema]:
        if admin:
            return await self.repo.adminp_get_listings_by_user_id(
                user_id, limit, offset
            )
        return await self.repo.get_listings_by_user_id(user_id, owner, limit, offset)

    async def get_favorite_listings(
        self, user_id: int, limit: int, offset: int
    ) -> Tuple[List[ShortListingSchema], int]:
        return await self.repo.get_favorite_listings(user_id, limit, offset)


class ListingService(IListingService):

    def __init__(self, repo: IListingRepository):
        self.repo = repo

    async def get_approved_listing_by_id(self, listing_id: int) -> Optional[ListingDTO]:
        return await self.repo.get_approved_listing_by_id(listing_id)

    async def get_listing_by_id(self, listing_id: int) -> ListingDTO:
        return await self.repo.get_listing_by_id(listing_id)

    async def reject_listing(
        self, listing_id: int, schema: RejectApplicationRequest
    ) -> None:
        return await self.repo.reject_listing_by_id(listing_id, schema.reason)

    async def approve_listing(self, listing_id: int) -> None:
        return await self.repo.approve_listing_by_id(listing_id)

    async def get_total_active_listings_count(self) -> int:
        return await self.repo.get_total_active_listings_count()

    async def get_active_listings_month_count(self) -> int:
        time_from = datetime.now(timezone.utc) - timedelta(days=30)
        return await self.repo.get_active_listings_month_count(time_from)

    async def get_refused_listings_count(self) -> int:
        return await self.repo.get_refused_listings_count()


class FavoriteListingService(IFavoriteListingService):
    def __init__(self, repo: IFavoriteListingRepository):
        self.repo = repo

    async def add_favorite(self, listing_id: int, user_id: int) -> None:
        try:
            await self.repo.add_favorite(listing_id, user_id)
        except IntegrityError:
            raise ListingIsAlreadyFavorite()

    async def remove_favorite(self, listing_id: int, user_id: int) -> None:
        await self.repo.remove_favorite(listing_id, user_id)

    async def get_user_favorite_listing_ids(
        self, user_id: int, listing_ids: List[int]
    ) -> List[int]:
        return await self.repo.get_user_favorite_ids(user_id, listing_ids)

    async def is_favorite(self, listing_id: int, user_id: int) -> bool:
        return await self.repo.is_listing_favorite(listing_id, user_id)
