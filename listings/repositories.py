import hashlib
import io
import os
import time
from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager
from datetime import datetime
from math import radians
from typing import Callable, List, Optional, Tuple

from fastapi import HTTPException, UploadFile
from PIL import Image
from sqlalchemy import and_, case, delete, exists, func, insert, or_, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, with_loader_criteria

from admin.schemas import ModerationApplication
from categories.models import Category, Subcategory
from core.logger import logger
from core.repositories import BaseRepository
from core.utils import generate_hashed_filename
from locations.models import Location
from promotions.models import PromotionOrder, PromotionTariff

from .mappers import ListingAggregateMapper, ListingMapper
from .models import FavoriteListing, Listing, ListingImage, ListingVideo
from .schemas import (
    AdminPShortListingSchema,
    CreateListingRequestSchema,
    GetListingsQuerySchema,
    ImageSchema,
    ListingAggregateDTO,
    ListingDTO,
    ListingSchema,
    ListingWithFavoriteFlag,
    ListingWithPriority,
    ShortListingSchema,
    ShortListingSchemaWithPriority,
    UpdateListingRequestSchema,
    VideoSchema,
)


class IListingRepository(ABC):
    @abstractmethod
    async def get_approved_listing_by_id(self, listing_id: int) -> Optional[ListingDTO]:
        pass

    @abstractmethod
    async def get_listing_by_id(self, listing_id: int) -> Optional[ListingDTO]:
        pass

    @abstractmethod
    async def reject_listing_by_id(self, listing_id: int, reason: str) -> None:
        pass

    @abstractmethod
    async def approve_listing_by_id(self, listing_id: int) -> None:
        pass

    @abstractmethod
    async def get_total_active_listings_count(self) -> int:
        pass

    @abstractmethod
    async def get_active_listings_month_count(self, time_from: datetime) -> int:
        pass

    @abstractmethod
    async def get_refused_listings_count(self) -> int:
        pass


class IListingAggregateRepository(ABC):

    @abstractmethod
    async def create_listing_aggregate(
        self,
        form_data: CreateListingRequestSchema,
        location_id: int,
        images: list,
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
        images: list,
        external_session: AsyncSession,
    ) -> ListingAggregateDTO:
        pass

    @abstractmethod
    async def get_listing_by_id(self, listing_id: int) -> Optional[ListingWithPriority]:
        pass

    @abstractmethod
    async def delete_listing_aggregate(
        self,
        listing_id: int,
        time_now: datetime,
        external_session: Optional[AsyncSession],
    ) -> None:
        pass

    @abstractmethod
    async def get_listing_images(self, listing_id: int) -> List[ImageSchema]:
        pass

    @abstractmethod
    async def get_active_listings(
        self, query
    ) -> Tuple[List[ShortListingSchemaWithPriority], int]:
        pass

    @abstractmethod
    async def get_all_listings(
        self, limit: int, offset: int
    ) -> Tuple[List[ShortListingSchema], int]:
        pass

    @abstractmethod
    async def get_unmoderated_listings(
        self, limit: int, offset: int
    ) -> Tuple[List[ModerationApplication], int]:
        pass

    @abstractmethod
    async def get_unmoderated_listing_by_id(
        self, listing_id: int
    ) -> Optional[ModerationApplication]:
        pass

    @abstractmethod
    async def get_listings_by_user_id(
        self, user_id: int, owner: bool, limit: int, offset: int
    ) -> List[ShortListingSchema]:
        pass

    @abstractmethod
    async def get_favorite_listings(
        self, user_id: int, limit: int, offset: int
    ) -> Tuple[List[ShortListingSchema], int]:
        pass

    @abstractmethod
    async def adminp_get_listings_by_user_id(
        self, user_id: int, limit: int, offset: int
    ) -> Tuple[List[AdminPShortListingSchema], int]:
        pass


class IFavoriteListingRepository(ABC):
    @abstractmethod
    async def add_favorite(self, listing_id: int, user_id: int) -> None:
        pass

    @abstractmethod
    async def remove_favorite(self, listing_id: int, user_id: int) -> None:
        pass

    @abstractmethod
    async def get_user_favorite_ids(
        self, user_id: int, listing_ids: List[int]
    ) -> List[int]:
        pass

    @abstractmethod
    async def is_listing_favorite(self, listing_id: int, user_id: int) -> bool:
        pass


class ListingRepository(IListingRepository, BaseRepository):

    async def get_approved_listing_by_id(self, listing_id: int) -> Optional[ListingDTO]:
        async with self.get_session() as session:
            results = await session.execute(
                select(Listing).where(
                    Listing.id == listing_id,
                    Listing.is_deleted == False,
                    Listing.moderation_status == "approved",
                )
            )
            listing = results.scalars().first()
            return ListingMapper.to_dto(listing) if listing else None

    async def get_listing_by_id(self, listing_id: int) -> Optional[ListingDTO]:
        async with self.get_session() as session:
            results = await session.execute(
                select(Listing).where(
                    Listing.id == listing_id, Listing.is_deleted == False
                )
            )
            listing = results.scalars().first()
            return ListingMapper.to_dto(listing) if listing else None

    async def reject_listing_by_id(self, listing_id: int, reason: str) -> None:
        async with self.get_session() as session:
            await session.execute(
                update(Listing)
                .where(
                    Listing.id == listing_id,
                    Listing.moderation_status == "pending",
                    Listing.is_deleted == False,
                )
                .values(moderation_status="rejected", reject_reason=reason)
            )
            await session.commit()

    async def approve_listing_by_id(self, listing_id: int) -> None:
        async with self.get_session() as session:
            await session.execute(
                update(Listing)
                .where(
                    Listing.id == listing_id,
                    Listing.moderation_status == "pending",
                    Listing.is_deleted == False,
                )
                .values(moderation_status="approved")
            )
            await session.commit()

    async def get_total_active_listings_count(self) -> int:
        async with self.get_session() as session:
            results = await session.execute(
                select(func.count(Listing.id)).where(
                    Listing.is_deleted == False, Listing.moderation_status == "approved"
                )
            )
            total_listings = results.scalar()
            return total_listings

    async def get_active_listings_month_count(self, time_from: datetime) -> int:
        async with self.get_session() as session:
            results = await session.execute(
                select(func.count(Listing.id)).where(
                    Listing.is_deleted == False,
                    Listing.moderation_status == "approved",
                    Listing.created_at >= time_from,
                )
            )
            total_listings = results.scalar()
            return total_listings

    async def get_refused_listings_count(self) -> int:
        async with self.get_session() as session:
            results = await session.execute(
                select(func.count(Listing.id)).where(
                    Listing.moderation_status == "rejected"
                )
            )
            refused_listings = results.scalar()
            return refused_listings


class ListingAggregateRepository(IListingAggregateRepository, BaseRepository):

    async def _create_listing(
        self,
        form_data: CreateListingRequestSchema,
        location_id: int,
        user_id: int,
        session: AsyncSession,
    ) -> Listing:
        listing = Listing(
            user_id=user_id,
            title=form_data.title,
            description=form_data.description,
            price=form_data.price,
            category_id=form_data.category_id,
            subcategory_id=form_data.subcategory_id,
            location_id=location_id,
        )
        session.add(listing)
        await session.flush()
        return listing

    async def _create_listing_images(
        self, listing_id: int, images: list[UploadFile], session: AsyncSession
    ) -> List[ImageSchema]:
        logger.warning(f"images imnages {images}")
        result_images = []

        # Создаем директорию для изображений, если она не существует
        os.makedirs("media/images", exist_ok=True)

        for image in images:
            # Проверка типа файла
            allowed_types = ["image/jpeg", "image/png", "image/heif"]
            if image.content_type not in allowed_types:
                raise HTTPException(status_code=422, detail="error.photo.invalid_type")

            logger.info(f"Uploading image {image.filename}")
            hashed_filename = generate_hashed_filename(image.filename)

            # Читаем содержимое файла
            content = await image.read()
            file_size = len(content)

            # Максимальный размер файла (5MB)
            max_size = 5 * 1024 * 1024

            # Если файл больше максимального размера, сжимаем его
            if file_size > max_size:
                image_pil = Image.open(io.BytesIO(content))

                # Начальные параметры
                max_dimension = 2000
                quality = 95

                while file_size > max_size and (quality > 20 or max_dimension > 800):
                    # Уменьшаем размер изображения, если оно все еще слишком большое
                    if max(image_pil.size) > max_dimension:
                        ratio = min(
                            max_dimension / max(image_pil.size[0], image_pil.size[1]),
                            1.0,
                        )
                        new_size = tuple(int(dim * ratio) for dim in image_pil.size)
                        image_pil = image_pil.resize(new_size, Image.Resampling.LANCZOS)

                    # Сжимаем с текущим качеством
                    output = io.BytesIO()
                    image_pil.save(
                        output, format="JPEG", quality=quality, optimize=True
                    )
                    content = output.getvalue()
                    file_size = len(content)

                    # Если размер все еще большой, уменьшаем качество и размер
                    if file_size > max_size:
                        quality -= 5
                        max_dimension = int(max_dimension * 0.9)

                    # Переоткрываем изображение для следующей итерации
                    if file_size > max_size:
                        image_pil = Image.open(io.BytesIO(content))

                if file_size > max_size:
                    raise HTTPException(status_code=422, detail="error.photo.too_large")

            file_location = f"media/images/{listing_id}_{hashed_filename}"
            with open(file_location, "wb") as file:
                file.write(content)

            listing_image = ListingImage(listing_id=listing_id, url=file_location)
            session.add(listing_image)
            logger.info(f"Image {image.filename} uploaded")
            await session.flush()
            logger.info(f"Image {image.filename} saved to database")
            result_images.append(ImageSchema(id=listing_image.id, url=file_location))
        return result_images

    async def _create_listing_video(
        self, listing_id: int, video: str, session: AsyncSession
    ) -> Optional[VideoSchema]:
        listing_video = ListingVideo(listing_id=listing_id, url=str(video))
        session.add(listing_video)
        await session.flush()
        return VideoSchema(id=listing_video.id, url=listing_video.url)

    async def create_listing_aggregate(
        self,
        form_data: CreateListingRequestSchema,
        location_id: int,
        images: List[UploadFile],
        user_id: int,
        session: AsyncSession,
    ) -> ListingAggregateDTO:
        async with self.get_session(session) as session:
            listing = await self._create_listing(
                form_data, location_id, user_id, session
            )
            logger.warning(f"Entering create listing images")
            images: List[ImageSchema] = await self._create_listing_images(
                listing.id, images, session
            )
            logger.warning(f"Images {images}")
            video = None
            if form_data.video:
                video: VideoSchema = await self._create_listing_video(
                    listing.id, form_data.video, session
                )
            if session.in_transaction():
                logger.info(f"Flushing")
                await session.flush()
            else:
                logger.info(f"Commiting")
                await session.commit()

        return ListingAggregateMapper.to_dto_with_photo_and_videos(
            listing, images, video
        )

    async def update_listing_aggregate(
        self,
        listing_id: int,
        form_data: UpdateListingRequestSchema,
        location_id: int,
        images: list[UploadFile],
        external_session: AsyncSession,
    ) -> ListingAggregateDTO:
        async with self.get_session(external_session) as session:
            listing = await session.get(Listing, listing_id)

            listing.title = form_data.title
            listing.description = form_data.description
            listing.price = form_data.price
            listing.category_id = form_data.category_id
            listing.subcategory_id = form_data.subcategory_id
            listing.location_id = location_id
            logger.warning(f"Images to delete {form_data.remove_image_ids}")
            if len(form_data.remove_image_ids) > 0:
                logger.warning(f"Deleting images with ids {form_data.remove_image_ids}")
                query = (
                    update(ListingImage)
                    .where(ListingImage.id.in_(form_data.remove_image_ids))
                    .values(is_deleted=True)
                )
                await session.execute(query)

            existing_images = await session.execute(
                select(ListingImage).where(
                    ListingImage.listing_id == listing_id,
                    ListingImage.is_deleted == False,
                )
            )
            existing_images = existing_images.scalars().all()

            existing_images_schemas = [
                ImageSchema(id=image.id, url=image.url) for image in existing_images
            ]

            if images:
                new_images = await self._create_listing_images(
                    listing_id, images, session
                )

                updated_images = existing_images_schemas + new_images
            else:
                updated_images = existing_images_schemas
            if form_data.remove_video:
                query = (
                    update(ListingVideo)
                    .where(ListingVideo.listing_id == listing_id)
                    .values(is_deleted=True)
                )
                await session.execute(query)

            video_schema = None
            if form_data.video:
                video_schema = await self._create_listing_video(
                    listing_id, form_data.video, session
                )

            if session.in_transaction():
                await session.flush()
            else:
                await session.commit()

            return ListingAggregateMapper.to_dto_with_photo_and_videos(
                listing, updated_images, video_schema
            )

    async def get_listing_by_id(self, listing_id: int) -> Optional[ListingWithPriority]:
        async with self.get_session() as session:
            query = (
                select(
                    Listing,
                    func.coalesce(PromotionTariff.priority, 0).label("priority"),
                )
                .where(Listing.id == listing_id, Listing.is_deleted == False)
                .outerjoin(
                    PromotionOrder,
                    and_(
                        PromotionOrder.listing_id == Listing.id,
                        PromotionOrder.status == "PAID",
                        PromotionOrder.start_date <= func.now(),
                        PromotionOrder.end_date >= func.now(),
                    ),
                )
                .outerjoin(
                    PromotionTariff, PromotionOrder.tariff_id == PromotionTariff.id
                )
                .options(
                    joinedload(Listing.images),
                    joinedload(Listing.video),
                    joinedload(Listing.location),
                    joinedload(Listing.category),
                    joinedload(Listing.subcategory),
                    joinedload(Listing.promotion_orders),
                    with_loader_criteria(
                        ListingImage,
                        lambda cls: cls.is_deleted == False,
                        include_aliases=True,
                    ),
                    with_loader_criteria(
                        ListingVideo,
                        lambda cls: cls.is_deleted == False,
                        include_aliases=True,
                    ),
                )
            )
            result = await session.execute(query)
            row = result.first()

            if not row:
                return None

            listing = row.Listing
            listing.priority = row.priority

            return ListingWithPriority.model_validate(listing)

    async def delete_listing_aggregate(
        self,
        listing_id: int,
        time_now: datetime,
        external_session: Optional[AsyncSession],
    ) -> None:
        async with self.get_session(external_session) as session:
            query_image = (
                update(ListingImage)
                .where(ListingImage.listing_id == listing_id)
                .values(is_deleted=True, deleted_at=time_now)
            )
            await session.execute(query_image)

            query_video = (
                update(ListingVideo)
                .where(ListingVideo.listing_id == listing_id)
                .values(is_deleted=True, deleted_at=time_now)
            )
            await session.execute(query_video)

            query_listing = (
                update(Listing)
                .where(Listing.id == listing_id)
                .values(is_deleted=True, deleted_at=time_now)
            )
            await session.execute(query_listing)

    async def get_listing_images(self, listing_id: int) -> List[ImageSchema]:
        async with self.get_session() as session:
            results = await session.execute(
                select(ListingImage).where(
                    ListingImage.listing_id == listing_id,
                    ListingImage.is_deleted == False,
                )
            )
            images = results.scalars().all()
            return [ImageSchema(id=image.id, url=image.url) for image in images]

    async def get_all_listings(
        self, limit: int, offset: int
    ) -> Tuple[List[ShortListingSchema], int]:
        async with self.get_session() as session:

            query = select(Listing)
            count_query = select(func.count()).select_from(query.subquery())
            count_result = await session.execute(count_query)
            total_count = count_result.scalar()

            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)

            results = await session.execute(
                query.options(
                    joinedload(Listing.location),
                    joinedload(Listing.images),
                    joinedload(Listing.video),
                )
            )

            listings = results.unique().scalars().all()
            short_dto_list = ListingAggregateMapper.to_short_dto_list(listings)
            return short_dto_list, total_count

    async def get_unmoderated_listings(
        self, limit: int, offset: int
    ) -> Tuple[List[ShortListingSchema], int]:
        async with self.get_session() as session:

            query = select(Listing).where(
                Listing.moderation_status == "pending", Listing.is_deleted == False
            )

            count_query = select(func.count()).select_from(query.subquery())
            count_result = await session.execute(count_query)
            total_count = count_result.scalar()

            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)

            results = await session.execute(
                query.options(
                    joinedload(Listing.location),
                    joinedload(Listing.images),
                    joinedload(Listing.video),
                    joinedload(Listing.user),
                )
            )

            listings = results.unique().scalars().all()
            application_list = ListingAggregateMapper.to_application_list(listings)
            return application_list, total_count

    async def get_unmoderated_listing_by_id(
        self, listing_id: int
    ) -> Optional[ModerationApplication]:
        async with self.get_session() as session:
            results = await session.execute(
                select(Listing)
                .where(
                    Listing.id == listing_id,
                    Listing.moderation_status == "pending",
                    Listing.is_deleted == False,
                )
                .options(
                    joinedload(Listing.images),
                    joinedload(Listing.video),
                    joinedload(Listing.user),
                )
            )
            listing = results.scalars().first()

            if not listing:
                return None

            return ListingAggregateMapper.to_application(listing)

    async def get_active_listings(
        self, query_params: GetListingsQuerySchema
    ) -> Tuple[List[ShortListingSchemaWithPriority], int]:
        async with self.get_session() as session:
            query_params_dict = query_params.dict()

            # Базовые параметры для сырого запроса
            params = {
                "latitude": query_params_dict.get("latitude"),
                "longitude": query_params_dict.get("longitude"),
                "limit": query_params_dict.get("limit", 10),
                "offset": query_params_dict.get("offset", 0),
            }

            # Добавление фильтров
            additional_filters = [
                "listings.is_sold = FALSE",
                "listings.moderation_status = 'approved'",
                "listings.is_deleted = FALSE",
            ]

            if query_params.category_id is not None:
                additional_filters.append("listings.category_id = :category_id")
                params["category_id"] = query_params.category_id
            if query_params.subcategory_id is not None:
                additional_filters.append("listings.subcategory_id = :subcategory_id")
                params["subcategory_id"] = query_params.subcategory_id
            if query_params.search:
                additional_filters.append(
                    "(listings.title ILIKE :search OR listings.description ILIKE :search)"
                )
                params["search"] = f"%{query_params.search}%"
            if query_params.price_min is not None:
                additional_filters.append("listings.price >= :price_min")
                params["price_min"] = query_params.price_min
            if query_params.price_max is not None:
                additional_filters.append("listings.price <= :price_max")
                params["price_max"] = query_params.price_max

            # Создание SQL-запроса с учетом фильтров
            additional_filters_clause = " AND ".join(additional_filters)

            # Определение порядка сортировки
            if params["latitude"] is not None and params["longitude"] is not None:
                order_clause = """
                    ORDER BY
                        CASE 
                            WHEN distance_50 <= 50 AND priority > 0 THEN 0
                            WHEN distance_50 <= 50 THEN 1
                            ELSE 2
                        END ASC,
                        distance_50 ASC
                """
            else:
                order_clause = "ORDER BY priority DESC"

            raw_query = f"""
                WITH listings_with_distance AS (
                    SELECT
                        listings.*,
                        locations.id AS location_id,
                        locations.address AS location_address,
                        locations.latitude AS location_latitude,
                        locations.longitude AS location_longitude,
                        6371 * ACOS(
                            COS(RADIANS(:latitude))
                            * COS(RADIANS(locations.latitude))
                            * COS(RADIANS(locations.longitude) - RADIANS(:longitude))
                            + SIN(RADIANS(:latitude)) * SIN(RADIANS(locations.latitude))
                        ) AS distance_50,
                        COALESCE(promotion_tariffs.priority, 0) AS priority,
                        ARRAY_AGG(
                            jsonb_build_object(
                                'id', listing_images.id,
                                'url', listing_images.url,
                                'created_at', listing_images.created_at,
                                'is_deleted', listing_images.is_deleted
                            )
                        ) FILTER (WHERE listing_images.is_deleted = FALSE) AS images
                    FROM listings
                    LEFT JOIN locations ON listings.location_id = locations.id
                    LEFT JOIN promotion_orders
                        ON promotion_orders.listing_id = listings.id
                        AND promotion_orders.status = 'PAID'
                        AND promotion_orders.start_date <= NOW()
                        AND promotion_orders.end_date >= NOW()
                    LEFT JOIN promotion_tariffs
                        ON promotion_orders.tariff_id = promotion_tariffs.id
                    LEFT JOIN listing_images ON listing_images.listing_id = listings.id
                    WHERE {additional_filters_clause}
                    GROUP BY listings.id, locations.id, promotion_tariffs.priority
                )
                SELECT *
                FROM listings_with_distance
                {order_clause}
                LIMIT :limit OFFSET :offset;
            """

            # Выполнение запроса
            result = await session.execute(text(raw_query), params)
            rows = result.fetchall()

            # Обработка результата
            listings = []
            for row in rows:
                row_dict = dict(row._mapping)

                distance_50 = row_dict.pop("distance_50", None)
                priority = row_dict.pop("priority", 0)

                location_data = {
                    "id": row_dict.pop("location_id", None),
                    "address": row_dict.pop("location_address", None),
                    "latitude": row_dict.pop("location_latitude", None),
                    "longitude": row_dict.pop("location_longitude", None),
                }

                # Извлечение изображений
                images_data = row_dict.pop("images", [])
                if images_data is None:
                    images_data = []
                images = [
                    ListingImage(
                        id=image["id"],
                        url=image["url"],
                        created_at=image["created_at"],
                        is_deleted=image["is_deleted"],
                    )
                    for image in images_data
                ]

                listing = Listing(**row_dict)  # ORM-поля
                listing.location = (
                    Location(**location_data) if location_data["id"] else None
                )
                listing.images = images
                listing.distance_50 = distance_50  # Кастомное поле
                listing.priority = priority  # Кастомное поле
                listings.append(listing)

            # Запрос на подсчет общего количества
            count_query = f"""
                WITH listings_with_distance AS (
                    SELECT 1
                    FROM listings
                    LEFT JOIN locations ON listings.location_id = locations.id
                    LEFT JOIN promotion_orders
                        ON promotion_orders.listing_id = listings.id
                        AND promotion_orders.status = 'PAID'
                        AND promotion_orders.start_date <= NOW()
                        AND promotion_orders.end_date >= NOW()
                    LEFT JOIN promotion_tariffs
                        ON promotion_orders.tariff_id = promotion_tariffs.id
                    LEFT JOIN listing_images ON listing_images.listing_id = listings.id
                    WHERE {additional_filters_clause}
                )
                SELECT COUNT(*) FROM listings_with_distance;
            """
            count_result = await session.execute(text(count_query), params)
            total_count = count_result.scalar() or 0

            # Преобразование в DTO
            short_dto_list = ListingAggregateMapper.to_short_dto_list_with_priorities(
                listings
            )

            return short_dto_list, total_count

    async def adminp_get_listings_by_user_id(
        self, user_id: int, limit: int, offset: int
    ) -> Tuple[List[AdminPShortListingSchema], int]:

        async with self.get_session() as session:
            query = (
                select(Listing)
                .options(joinedload(Listing.images), joinedload(Listing.location))
                .where(
                    Listing.user_id == user_id,
                )
            )

            total_count_query = select(func.count()).select_from(query.subquery())
            total_count_result = await session.execute(total_count_query)
            total_count = total_count_result.scalar()

            paginated_query = query.limit(limit).offset(offset)
            results = await session.execute(paginated_query)

            listings = results.unique().scalars().all()
            short_dto_list = ListingAggregateMapper.to_short_adminp_dto_list(listings)
            return short_dto_list, total_count

    async def get_listings_by_user_id(
        self, user_id: int, owner: bool, limit: int, offset: int
    ) -> Tuple[List[ShortListingSchema], int]:
        async with self.get_session() as session:
            query = (
                select(Listing)
                .options(joinedload(Listing.images), joinedload(Listing.location))
                .where(
                    Listing.user_id == user_id,
                    Listing.is_deleted == False,
                    Listing.is_sold == False,
                )
            )
            if not owner:
                query = query.where(Listing.moderation_status == "approved")

            total_count_query = select(func.count()).select_from(query.subquery())
            total_count_result = await session.execute(total_count_query)
            total_count = total_count_result.scalar()

            paginated_query = query.limit(limit).offset(offset)
            results = await session.execute(paginated_query)

            listings = results.unique().scalars().all()
            if not owner:
                short_dto_list = ListingAggregateMapper.to_short_dto_list(listings)
            else:
                short_dto_list = ListingAggregateMapper.to_my_short_dto_list(listings)
            return short_dto_list, total_count

    async def get_favorite_listings(
        self, user_id: int, limit: int, offset: int
    ) -> List[ShortListingSchema]:
        async with self.get_session() as session:
            query = (
                select(FavoriteListing)
                .join(Listing, FavoriteListing.listing_id == Listing.id)
                .options(
                    joinedload(FavoriteListing.listing).joinedload(Listing.images),
                    joinedload(FavoriteListing.listing).joinedload(Listing.location),
                )
                .where(
                    FavoriteListing.user_id == user_id,
                    Listing.is_deleted == False,
                    Listing.is_sold == False,
                )
            )

            total_count_query = select(func.count()).select_from(query.subquery())
            total_count_result = await session.execute(total_count_query)
            total_count = total_count_result.scalar()

            paginated_query = query.limit(limit).offset(offset)
            results = await session.execute(paginated_query)

            favorite_listings = results.unique().scalars().all()
            listings = [
                favorite_listing.listing for favorite_listing in favorite_listings
            ]
            short_dto_list = ListingAggregateMapper.to_short_dto_list(listings)
            logger.warning(f"Short dto list {short_dto_list}")
            return short_dto_list, total_count


class FavoriteListingRepository(IFavoriteListingRepository, BaseRepository):

    async def add_favorite(self, listing_id: int, user_id: int) -> None:
        async with self.get_session() as session:
            await session.execute(
                insert(FavoriteListing).values(listing_id=listing_id, user_id=user_id)
            )
            await session.commit()

    async def remove_favorite(self, listing_id: int, user_id: int) -> None:
        async with self.get_session() as session:
            await session.execute(
                delete(FavoriteListing).where(
                    FavoriteListing.listing_id == listing_id,
                    FavoriteListing.user_id == user_id,
                )
            )
            await session.commit()

    async def get_user_favorite_ids(
        self, user_id: int, listing_ids: List[int]
    ) -> List[int]:
        async with self.get_session() as session:
            results = await session.execute(
                select(FavoriteListing.listing_id)
                .where(FavoriteListing.user_id == user_id)
                .where(FavoriteListing.listing_id.in_(listing_ids))
            )

            return [row.listing_id for row in results]

    async def is_listing_favorite(self, listing_id: int, user_id: int) -> bool:
        async with self.get_session() as session:
            result = await session.execute(
                select(
                    exists().where(
                        FavoriteListing.listing_id == listing_id,
                        FavoriteListing.user_id == user_id,
                    )
                )
            )
            return result.scalar()
