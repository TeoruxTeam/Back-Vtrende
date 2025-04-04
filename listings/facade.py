from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from fastapi import UploadFile

from categories.exceptions import CategoryNotFound, SubcategoryNotFound
from categories.schemas import (
    CategorySchema,
    CategoryWithLocalization,
    SubcategorySchema,
    SubcategoryWithLocalization,
)
from categories.services import ICategoryService, ISubcategoryService
from core.database import IUnitOfWork
from core.logger import logger
from core.utils import get_media_url
from locations.schemas import LocationDTO
from locations.services import ILocationService
from users.schemas import UserDTO

from .exceptions import (
    ListingNotFound,
    NotEnoughImages,
    TooManyImages,
    UnableToFavoriteYourOwnListing,
)
from .schemas import (
    AddToFavoritesRequestSchema,
    AddToFavoritesResponseSchema,
    CreateListingRequestSchema,
    CreateListingResponseSchema,
    GetListingResponseSchema,
    GetListingsQuerySchema,
    GetListingsResponseSchema,
    GetMyFavoritesResponseSchema,
    GetMyListingsResponseSchema,
    GetUserListingsResponseSchema,
    ImageSchema,
    ListingAggregateDTO,
    ListingDTO,
    ListingSchema,
    ListingWithFavoriteFlag,
    RemoveFromFavoritesRequestSchema,
    RemoveFromFavoritesResponseSchema,
    ShortListingSchema,
    ShortListingWithFavoriteFlag,
    ShortListingWithFavoriteFlagAndPriority,
    UpdateListingRequestSchema,
    UpdateListingResponseSchema,
)
from .services import IFavoriteListingService, IListingAggregateService, IListingService


class IListingFacade(ABC):

    @abstractmethod
    async def create_listing(
        self,
        form_data: CreateListingRequestSchema,
        images: List[UploadFile],
        current_user: UserDTO,
        base_url: str,
        language: str,
    ) -> CreateListingResponseSchema:
        pass

    @abstractmethod
    async def get_listings(
        self, query: GetListingsQuerySchema, base_url: str, user: Optional[UserDTO]
    ) -> GetListingsResponseSchema:
        pass

    @abstractmethod
    async def get_short_listing_by_id(self, listing_id: int) -> ListingDTO:
        pass

    @abstractmethod
    async def get_listing_by_id(
        self, listing_id: int, user: Optional[UserDTO], base_url: str, language: str
    ) -> GetListingResponseSchema:
        pass

    @abstractmethod
    async def update_listing(
        self,
        listing_id: int,
        form_data: UpdateListingRequestSchema,
        images: List[UploadFile],
        current_user: UserDTO,
        base_url: str,
        language: str,
    ):
        pass

    @abstractmethod
    async def delete_listing(self, listing_id: int, current_user: UserDTO) -> None:
        pass

    @abstractmethod
    async def get_my_listings(
        self, user: UserDTO, limit: int, offset: int, base_url: str
    ) -> GetMyListingsResponseSchema:
        pass

    @abstractmethod
    async def get_user_listings(
        self,
        user_id: int,
        limit: int,
        offset: int,
        base_url: str,
        user: Optional[UserDTO],
    ) -> GetUserListingsResponseSchema:
        pass

    @abstractmethod
    async def add_to_favorites(
        self, schema: AddToFavoritesRequestSchema, user: UserDTO
    ) -> AddToFavoritesResponseSchema:
        pass

    @abstractmethod
    async def remove_from_favorites(
        self, schema: RemoveFromFavoritesRequestSchema, user: UserDTO
    ) -> RemoveFromFavoritesResponseSchema:
        pass

    @abstractmethod
    async def get_favorites(
        self, user: UserDTO, limit: int, offset: int, base_url: str
    ) -> GetMyFavoritesResponseSchema:
        pass


class ListingFacade(IListingFacade):

    def __init__(
        self,
        listing_service: IListingService,
        listing_aggregate_service: IListingAggregateService,
        location_service: ILocationService,
        category_service: ICategoryService,
        subcategory_service: ISubcategoryService,
        favorite_listing_service: IFavoriteListingService,
        uow: IUnitOfWork,
    ):
        self.listing_service = listing_service
        self.listing_aggregate_service = listing_aggregate_service
        self.location_service = location_service
        self.category_service = category_service
        self.subcategory_service = subcategory_service
        self.favorite_listing_service = favorite_listing_service
        self.uow = uow

    def _validate_images_limit(
        self,
        existing_images: List[ImageSchema],
        new_images: List[UploadFile],
        remove_image_ids: List[int],
    ):
        if not new_images:
            new_images = []

        """Валидация количества фотографий после учёта удаления и добавления новых."""
        total_images = len(existing_images)

        existing_image_ids = {image.id for image in existing_images}
        logger.warning(f"remove image ids {remove_image_ids}")
        logger.warning(f"existing images: {existing_image_ids}")
        valid_remove_image_ids = [
            image_id for image_id in remove_image_ids if image_id in existing_image_ids
        ]
        logger.warning(f"valid remove image ids {valid_remove_image_ids}")
        remaining_images = total_images - len(valid_remove_image_ids)
        logger.warning(f"remaining images {remaining_images}")
        if remaining_images + len(new_images) <= 0:
            raise NotEnoughImages()

        if remaining_images + len(new_images) > 5:
            raise TooManyImages()

    async def create_listing(
        self,
        form_data: CreateListingRequestSchema,
        images: List[UploadFile],
        current_user: UserDTO,
        base_url: str,
        language: str,
    ) -> CreateListingResponseSchema:
        await self.uow.begin()
        session = await self.uow.get_session()
        category: CategoryWithLocalization = (
            await self.category_service.get_category_with_localization_by_id(
                form_data.category_id, language
            )
        )
        if not category:
            raise CategoryNotFound

        if form_data.subcategory_id:
            subcategory: SubcategoryWithLocalization = (
                await self.subcategory_service.get_subcategory_with_localization_by_id(
                    form_data.subcategory_id, language
                )
            )
            if not subcategory or subcategory.category_id != category.id:
                raise SubcategoryNotFound

        location: LocationDTO = await self.location_service.get_or_create_location(
            form_data.latitude, form_data.longitude, session
        )

        listing_aggregate_dto: ListingAggregateDTO = (
            await self.listing_aggregate_service.create_listing_aggregate(
                form_data, location.id, images, current_user.id, session
            )
        )
        await self.uow.commit()
        for image in listing_aggregate_dto.images:
            image.url = get_media_url(base_url, image.url)
        if listing_aggregate_dto.video:
            listing_aggregate_dto.video.url = get_media_url(
                base_url, listing_aggregate_dto.video.url
            )
        listing_schema = ListingSchema(
            location={**location.dict()},
            category_name=category.localized_name,
            subcategory_name=(
                subcategory.localized_name if form_data.subcategory_id else None
            ),
            **listing_aggregate_dto.dict(),
        )
        return CreateListingResponseSchema(data=listing_schema)

    async def get_listings(
        self, query: GetListingsQuerySchema, base_url: str, user: Optional[UserDTO]
    ) -> GetListingsResponseSchema:
        listings, count = await self.listing_aggregate_service.get_active_listings(
            query
        )
        logger.error(f"listings {listings}")
        listing_ids = [listing.id for listing in listings]

        if user:
            logger.info(f"Authorized user requested get listings")
            favorite_listing_ids = (
                await self.favorite_listing_service.get_user_favorite_listing_ids(
                    user.id, listing_ids
                )
            )
            logger.info(f"Favorite listings ids are {favorite_listing_ids}")
        else:
            logger.info(f"Unauthorized user requested listings")
            favorite_listing_ids = set()

        response_listings = []
        for listing in listings:
            for image in listing.images:
                image.url = get_media_url(base_url, image.url)
            logger.info(f"Listing id {listing.id} and favorites {favorite_listing_ids}")
            response_listings.append(
                ShortListingWithFavoriteFlagAndPriority(
                    **listing.dict(), is_favorite=listing.id in favorite_listing_ids
                )
            )

        return GetListingsResponseSchema(data=response_listings, count=count)

    async def get_short_listing_by_id(self, listing_id: int) -> ListingDTO:
        listing: ListingDTO = await self.listing_service.get_approved_listing_by_id(
            listing_id
        )
        if not listing:
            raise ListingNotFound
        return listing

    async def get_listing_by_id(
        self, listing_id: int, user: Optional[UserDTO], base_url: str, language: str
    ) -> GetListingResponseSchema:
        listing: ListingSchema = await self.listing_service.get_listing_by_id(
            listing_id
        )
        if not listing or (
            listing.moderation_status != "approved"
            and (not user or user.id != listing.user_id)
        ):
            raise ListingNotFound

        category: CategoryWithLocalization = (
            await self.category_service.get_category_with_localization_by_id(
                listing.category_id, language
            )
        )
        if listing.subcategory_id:
            subcategory: SubcategoryWithLocalization = (
                await self.subcategory_service.get_subcategory_with_localization_by_id(
                    listing.subcategory_id, language
                )
            )
        else:
            subcategory = None
        listing_aggregate_dto = (
            await self.listing_aggregate_service.get_listing_by_id(listing_id)
        )
        for image in listing_aggregate_dto.images:
            image.url = get_media_url(base_url, image.url)
        if listing_aggregate_dto.video:
            listing_aggregate_dto.video.url = get_media_url(
                base_url, listing_aggregate_dto.video.url
            )

        if user:
            is_favorite = await self.favorite_listing_service.is_favorite(
                listing_aggregate_dto.id, user.id
            )
        else:
            is_favorite = False

        return GetListingResponseSchema(
            data={
                **listing_aggregate_dto.dict(),
                "category_name": category.localized_name,
                "subcategory_name": subcategory.localized_name if subcategory else None,
                "is_favorite": is_favorite,
            }
        )

    async def update_listing(
        self,
        listing_id: int,
        form_data: UpdateListingRequestSchema,
        images: List[UploadFile],
        current_user: UserDTO,
        base_url: str,
        language: str,
    ) -> UpdateListingResponseSchema:
        await self.uow.begin()
        session = await self.uow.get_session()

        listing: ListingDTO = await self.listing_service.get_listing_by_id(listing_id)
        if not listing or listing.user_id != current_user.id:
            raise ListingNotFound

        existing_images = await self.listing_aggregate_service.get_listing_images(
            listing_id
        )
        self._validate_images_limit(existing_images, images, form_data.remove_image_ids)

        category: CategoryWithLocalization = (
            await self.category_service.get_category_with_localization_by_id(
                form_data.category_id, language
            )
        )
        if not category:
            raise CategoryNotFound

        subcategory: SubcategoryWithLocalization = (
            await self.subcategory_service.get_subcategory_with_localization_by_id(
                form_data.subcategory_id, language
            )
        )
        if not subcategory or subcategory.category_id != category.id:
            raise SubcategoryNotFound

        if form_data.video:
            form_data.remove_video = True
        # локации едины для одинаковых координат, поэтому полезно будет каждый раз создавать их, а не изменять предыдущие
        location: LocationDTO = await self.location_service.get_or_create_location(
            form_data.latitude, form_data.longitude, session
        )

        listing_aggregate_dto: ListingAggregateDTO = (
            await self.listing_aggregate_service.update_listing_aggregate(
                listing_id, form_data, location.id, images, session
            )
        )
        await self.uow.commit()
        logger.warning(f"Listing updated: {listing_aggregate_dto}")
        for image in listing_aggregate_dto.images:
            image.url = get_media_url(base_url, image.url)
        if listing_aggregate_dto.video:
            listing_aggregate_dto.video.url = get_media_url(
                base_url, listing_aggregate_dto.video.url
            )
        listing_schema = ListingSchema(
            location={**location.dict()},
            category_name=category.localized_name,
            subcategory_name=subcategory.localized_name,
            **listing_aggregate_dto.dict(),
        )
        return UpdateListingResponseSchema(data=listing_schema)

    async def delete_listing(self, listing_id: int, current_user: UserDTO) -> None:
        await self.uow.begin()
        session = await self.uow.get_session()

        listing: ListingDTO = await self.listing_service.get_listing_by_id(listing_id)
        if not listing or listing.user_id != current_user.id:
            raise ListingNotFound

        await self.listing_aggregate_service.delete_listing_aggregate(
            listing_id, session
        )

        await self.uow.commit()

    async def get_my_listings(
        self, user: UserDTO, limit: int, offset: int, base_url: str
    ) -> GetMyListingsResponseSchema:
        owner = True
        listings, count = await self.listing_aggregate_service.get_listings_by_user_id(
            user.id, owner, False, limit, offset
        )
        for listing in listings:
            for image in listing.images:
                image.url = get_media_url(base_url, image.url)
        return GetMyListingsResponseSchema(data=listings, count=count)

    async def get_user_listings(
        self,
        user_id: int,
        limit: int,
        offset: int,
        base_url: str,
        user: Optional[UserDTO],
    ) -> GetUserListingsResponseSchema:
        owner = False
        listings, count = await self.listing_aggregate_service.get_listings_by_user_id(
            user_id, owner, False, limit, offset
        )
        listing_ids = [listing.id for listing in listings]
        response_listings = []

        if user:
            favorite_listing_ids = (
                await self.favorite_listing_service.get_user_favorite_listing_ids(
                    user.id, listing_ids
                )
            )
        else:
            favorite_listing_ids = set()

        for listing in listings:
            for image in listing.images:
                image.url = get_media_url(base_url, image.url)

            response_listings.append(
                ShortListingWithFavoriteFlag(
                    **listing.dict(), is_favorite=listing.id in favorite_listing_ids
                )
            )

        return GetUserListingsResponseSchema(data=response_listings, count=count)

    async def add_to_favorites(
        self, schema: AddToFavoritesRequestSchema, user: UserDTO
    ) -> AddToFavoritesResponseSchema:
        listing = await self.listing_service.get_approved_listing_by_id(
            schema.listing_id
        )
        if not listing:
            raise ListingNotFound()
        if listing.user_id == user.id:
            raise UnableToFavoriteYourOwnListing()

        await self.favorite_listing_service.add_favorite(schema.listing_id, user.id)
        return AddToFavoritesResponseSchema()

    async def remove_from_favorites(
        self, schema: RemoveFromFavoritesRequestSchema, user: UserDTO
    ) -> RemoveFromFavoritesResponseSchema:
        await self.favorite_listing_service.remove_favorite(schema.listing_id, user.id)
        return RemoveFromFavoritesResponseSchema()

    async def get_favorites(
        self, user: UserDTO, limit: int, offset: int, base_url: str
    ) -> GetMyFavoritesResponseSchema:
        favorites, count = await self.listing_aggregate_service.get_favorite_listings(
            user.id, limit, offset
        )

        response_favorites = []

        for favorite in favorites:
            for image in favorite.images:
                image.url = get_media_url(base_url, image.url)

            response_favorites.append(
                ShortListingWithFavoriteFlag(**favorite.dict(), is_favorite=True)
            )

        return GetMyFavoritesResponseSchema(data=response_favorites, count=count)
