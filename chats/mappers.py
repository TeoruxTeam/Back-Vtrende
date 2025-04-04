from datetime import datetime
from typing import List, Optional

from listings.mappers import ListingMapper

from .models import ListingChat, ListingChatMessage
from .schemas import (
    ChatDTO,
    ChatMessageDTO,
    ChatWithListingDTO,
    DetailChatSchema,
    ShortChatSchema,
)


class ChatMapper:
    @staticmethod
    def to_dto(chat: ListingChat):
        return ChatDTO(
            id=chat.id,
            listing_id=chat.listing_id,
            buyer_id=chat.buyer_id,
            created_at=chat.created_at,
        )

    @staticmethod
    def to_dto_with_listing(chat: ListingChat):
        return ChatWithListingDTO(
            id=chat.id,
            listing_id=chat.listing_id,
            buyer_id=chat.buyer_id,
            created_at=chat.created_at,
            listing=ListingMapper.to_dto(chat.listing),
        )

    @staticmethod
    def to_short_schema_list(
        chats_with_data: List[tuple[ListingChat, datetime, datetime]], user_id: int
    ) -> List[ShortChatSchema]:
        return [
            ShortChatSchema(
                id=chat.id,
                interlocutor_id=(
                    chat.buyer_id
                    if chat.listing.user_id == user_id
                    else chat.listing.user_id
                ),
                interlocutor_name=(
                    chat.buyer.name
                    if chat.listing.user_id == user_id
                    else chat.listing.user.name
                ),
                interlocutor_avatar=(
                    chat.buyer.avatar
                    if chat.listing.user_id == user_id
                    else chat.listing.user.avatar
                ),
                listing_id=chat.listing_id,
                listing_name=chat.listing.title,
                listing_photo=(
                    next(
                        (
                            img.url
                            for img in sorted(
                                chat.listing.images, key=lambda i: i.created_at
                            )
                            if not img.is_deleted
                        ),
                        None,
                    )
                    if chat.listing.images
                    else None
                ),
                listing_price=chat.listing.price,
                last_message_text=last_message_text,
                last_message_created_at=last_message_datetime,
                earliest_image_created_at=earliest_image_datetime,
                unread_messages_count=unread_messages_count,
            )
            for chat, last_message_datetime, last_message_text, earliest_image_datetime, unread_messages_count in chats_with_data
        ]

    @staticmethod
    def to_short_schema(
        chat: ListingChat,
        user_id: int,
        last_message_datetime: datetime = None,
        last_message_text: str = None,
        earliest_image_datetime: datetime = None,
        unread_messages_count: int = 0,
    ) -> ShortChatSchema:
        return ShortChatSchema(
            id=chat.id,
            interlocutor_id=(
                chat.buyer_id
                if chat.listing.user_id == user_id
                else chat.listing.user_id
            ),
            interlocutor_name=(
                chat.buyer.name
                if chat.listing.user_id == user_id
                else chat.listing.user.name
            ),
            interlocutor_avatar=(
                chat.buyer.avatar
                if chat.listing.user_id == user_id
                else chat.listing.user.avatar
            ),
            listing_id=chat.listing_id,
            listing_name=chat.listing.title,
            listing_photo=(
                next(
                    (
                        img.url
                        for img in sorted(
                            chat.listing.images, key=lambda i: i.created_at
                        )
                        if not img.is_deleted
                    ),
                    None,
                )
                if chat.listing.images
                else None
            ),
            listing_price=chat.listing.price,
            last_message_text=last_message_text,
            last_message_created_at=last_message_datetime,
            earliest_image_created_at=earliest_image_datetime,
            unread_messages_count=unread_messages_count,
        )

    @staticmethod
    def to_detail_schema(
        chat: ListingChat,
        earliest_image_datetime: Optional[datetime],
        messages: List[ListingChatMessage],
        total_count: int,
        user_id: int,
    ) -> Optional[DetailChatSchema]:
        is_user_seller = chat.listing.user_id == user_id
        return DetailChatSchema(
            id=chat.id,
            interlocutor_id=chat.buyer_id if is_user_seller else chat.listing.user_id,
            interlocutor_name=(
                chat.buyer.name if is_user_seller else chat.listing.user.name
            ),
            interlocutor_avatar=(
                chat.buyer.avatar if is_user_seller else chat.listing.user.avatar
            ),
            listing_id=chat.listing_id,
            listing_name=chat.listing.title,
            listing_photo=(
                next(
                    (
                        img.url
                        for img in sorted(
                            chat.listing.images, key=lambda i: i.created_at
                        )
                        if not img.is_deleted
                    ),
                    None,
                )
                if chat.listing.images
                else None
            ),
            listing_price=chat.listing.price,
            earliest_image_datetime=earliest_image_datetime,
            last_message_created_at=messages[-1].created_at if messages else None,
            last_message_text=messages[-1].message if messages else None,
            messages=ChatMessageMapper.to_dto_list(messages),
            count=total_count,
        )


class ChatMessageMapper:
    @staticmethod
    def to_dto(message: ListingChatMessage) -> ChatMessageDTO:
        return ChatMessageDTO(
            id=message.id,
            chat_id=message.chat_id,
            user_id=message.user_id,
            message=message.message,
            created_at=message.created_at,
        )

    @staticmethod
    def to_dto_list(messages: List[ListingChatMessage]) -> List[ChatMessageDTO]:
        return [
            ChatMessageDTO(
                id=message.id,
                chat_id=message.chat_id,
                user_id=message.user_id,
                message=message.message,
                created_at=message.created_at,
            )
            for message in messages
        ]
