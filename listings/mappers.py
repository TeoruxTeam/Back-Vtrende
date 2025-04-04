from typing import List, Optional

from admin.schemas import ModerationApplication

from .models import Listing
from .schemas import (
    AdminPShortListingSchema,
    ImageSchema,
    ListingAggregateDTO,
    ListingDTO,
    LocationSchema,
    MyShortListingSchema,
    ShortListingSchema,
    ShortListingSchemaWithPriority,
    VideoSchema,
)


class ListingMapper:
    @staticmethod
    def to_dto(listing: Listing) -> ListingDTO:
        return ListingDTO(
            id=listing.id,
            user_id=listing.user_id,
            title=listing.title,
            description=listing.description,
            price=listing.price,
            category_id=listing.category_id,
            subcategory_id=listing.subcategory_id,
            created_at=listing.created_at,
            moderation_status=listing.moderation_status,
        )


class ListingAggregateMapper:
    @staticmethod
    def to_dto(listing: Listing) -> ListingAggregateDTO:
        return ListingAggregateDTO(
            id=listing.id,
            user_id=listing.user_id,
            title=listing.title,
            description=listing.description,
            price=listing.price,
            category_id=listing.category_id,
            subcategory_id=listing.subcategory_id,
            images=[
                ImageSchema(id=image.id, url=image.url)
                for image in listing.images
                if not image.is_deleted
            ],
            video=(
                VideoSchema(id=listing.video.id, url=listing.video.url)
                if listing.video
                else None
            ),
            created_at=listing.created_at,
            moderation_status=listing.moderation_status,
            deleted_at=listing.deleted_at,
            is_deleted=listing.is_deleted,
            is_sold=listing.is_sold,
            sold_at=listing.sold_at,
        )

    @staticmethod
    def to_dto_with_photo_and_videos(
        listing, images: List[ImageSchema], video: VideoSchema
    ) -> ListingAggregateDTO:
        return ListingAggregateDTO(
            id=listing.id,
            user_id=listing.user_id,
            title=listing.title,
            description=listing.description,
            price=listing.price,
            category_id=listing.category_id,
            subcategory_id=listing.subcategory_id,
            images=images,
            video=video,
            created_at=listing.created_at,
            moderation_status=listing.moderation_status,
            deleted_at=listing.deleted_at,
            is_deleted=listing.is_deleted,
            is_sold=listing.is_sold,
            sold_at=listing.sold_at,
        )

    @staticmethod
    def to_short_dto_list(listings: List[Listing]) -> List[ShortListingSchema]:
        return [
            ShortListingSchema(
                id=listing.id,
                title=listing.title,
                price=listing.price,
                images=[
                    ImageSchema(id=image.id, url=image.url)
                    for image in sorted(listing.images, key=lambda img: img.id)[:5]
                    if not image.is_deleted
                ],
                location=LocationSchema(
                    address=listing.location.address,
                    latitude=listing.location.latitude,
                    longitude=listing.location.longitude,
                ),
                created_at=listing.created_at,
                moderation_status=listing.moderation_status,
                is_sold=listing.is_sold,
                seller_id=listing.user_id,
                sold_at=listing.sold_at,
            )
            for listing in listings
        ]

    @staticmethod
    def to_short_dto_list_with_priorities(
        listings: List[Listing],
    ) -> List[ShortListingSchemaWithPriority]:
        return [
            ShortListingSchemaWithPriority(
                id=listing.id,
                title=listing.title,
                price=listing.price,
                images=[
                    ImageSchema(id=image.id, url=image.url)
                    for image in sorted(
                        listing.images, key=lambda img: img.created_at, reverse=True
                    )[:5]
                    if not image.is_deleted
                ],
                location=LocationSchema(
                    address=listing.location.address,
                    latitude=listing.location.latitude,
                    longitude=listing.location.longitude,
                ),
                created_at=listing.created_at,
                moderation_status=listing.moderation_status,
                is_sold=listing.is_sold,
                seller_id=listing.user_id,
                sold_at=listing.sold_at,
                priority=listing.priority,
            )
            for listing in listings
        ]

    @staticmethod
    def to_my_short_dto_list(listings: List[Listing]) -> List[MyShortListingSchema]:
        return [
            MyShortListingSchema(
                id=listing.id,
                title=listing.title,
                price=listing.price,
                images=[
                    ImageSchema(id=image.id, url=image.url)
                    for image in sorted(listing.images, key=lambda img: img.id)[:5]
                    if not image.is_deleted
                ],
                location=LocationSchema(
                    address=listing.location.address,
                    latitude=listing.location.latitude,
                    longitude=listing.location.longitude,
                ),
                created_at=listing.created_at,
                moderation_status=listing.moderation_status,
                reject_reason=listing.reject_reason,
                is_sold=listing.is_sold,
                seller_id=listing.user_id,
                sold_at=listing.sold_at,
            )
            for listing in listings
        ]

    @staticmethod
    def to_application_list(listings: List[Listing]) -> List[ModerationApplication]:
        return [
            ModerationApplication(
                id=listing.id,
                title=listing.title,
                username=listing.user.name
                + ((" " + listing.user.surname) if listing.user.surname else ""),
                created_at=listing.created_at,
                images=[
                    ImageSchema(id=image.id, url=image.url)
                    for image in sorted(
                        listing.images, key=lambda img: img.created_at, reverse=True
                    )[:5]
                ],
                video=(
                    VideoSchema(id=listing.video.id, url=listing.video.url)
                    if listing.video
                    else None
                ),
            )
            for listing in listings
        ]

    @staticmethod
    def to_application(listing: Listing) -> ModerationApplication:
        return ModerationApplication(
            id=listing.id,
            title=listing.title,
            username=listing.user.name
            + ((" " + listing.user.surname) if listing.user.surname else ""),
            created_at=listing.created_at,
            images=[
                ImageSchema(id=image.id, url=image.url)
                for image in sorted(
                    listing.images, key=lambda img: img.created_at, reverse=True
                )[:5]
            ],
            video=(
                VideoSchema(id=listing.video.id, url=listing.video.url)
                if listing.video
                else None
            ),
        )

    @staticmethod
    def to_short_adminp_dto_list(
        listings: List[Listing],
    ) -> List[AdminPShortListingSchema]:
        return [
            AdminPShortListingSchema(
                id=listing.id,
                title=listing.title,
                price=listing.price,
                images=[
                    ImageSchema(id=image.id, url=image.url)
                    for image in sorted(
                        listing.images, key=lambda img: img.created_at, reverse=True
                    )[:5]
                ],
                location=LocationSchema(
                    address=listing.location.address,
                    latitude=listing.location.latitude,
                    longitude=listing.location.longitude,
                ),
                created_at=listing.created_at,
                moderation_status=listing.moderation_status,
                is_sold=listing.is_sold,
                sold_at=listing.sold_at,
                is_deleted=listing.is_deleted,
                seller_id=listing.user_id,
                deleted_at=listing.deleted_at,
            )
            for listing in listings
        ]
