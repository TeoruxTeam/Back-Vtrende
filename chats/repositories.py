from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from sqlalchemy import distinct, func, or_, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload

from core.logger import logger
from core.repositories import BaseRepository
from items.models import Listing, ListingImage

from .exceptions import ChatNotFound
from .mappers import ChatMapper, ChatMessageMapper
from .models import ListingChat, ListingChatMessage
from .schemas import (
    ChatDTO,
    ChatMessageDTO,
    ChatWithListingDTO,
    DetailChatSchema,
    ShortChatSchema,
)


class IMessageRepository(ABC):
    @abstractmethod
    async def get_messages(self, chat_id: int):
        pass

    @abstractmethod
    async def create_message(
        self, chat_id: int, user_id: int, message: str
    ) -> ChatMessageDTO:
        pass

    @abstractmethod
    async def read_messages(self, chat_id: int, user_id: int) -> None:
        pass


class IChatRepository(ABC):

    @abstractmethod
    async def create_chat(self, buyer_id: int, listing_id: int) -> ChatDTO:
        pass

    @abstractmethod
    async def get_chat_by_listing_and_buyer(
        self, listing_id: int, buyer_id: int
    ) -> Optional[ChatDTO]:
        pass

    @abstractmethod
    async def get_chat_by_buyer_and_listing_ids(
        self, buyer_id: int, listing_id: int
    ) -> Optional[ChatDTO]:
        pass

    @abstractmethod
    async def get_chat_with_listing_by_id(
        self, chat_id: int
    ) -> Optional[ChatWithListingDTO]:
        pass

    @abstractmethod
    async def get_user_chats(
        self, user_id: int, limit: int, offset: int
    ) -> Tuple[List[ShortChatSchema], int, int]:
        pass

    @abstractmethod
    async def get_user_chat(self, user_id: int, chat_id: int) -> ShortChatSchema:
        pass


class IChatAggregateRepository(ABC):
    @abstractmethod
    async def get_detail_chat_by_id(
        self, chat_id: int, user_id: int, limit: int, offset: int
    ) -> Optional[DetailChatSchema]:
        pass


class MessageRepository(IMessageRepository, BaseRepository):

    async def get_messages(self, chat_id: int):
        pass

    async def create_message(
        self, chat_id: int, user_id: int, message: str
    ) -> ChatMessageDTO:
        async with self.get_session() as session:
            try:
                message = ListingChatMessage(
                    chat_id=chat_id, user_id=user_id, message=message
                )
                session.add(message)
                await session.commit()
                await session.refresh(message)
                message = ChatMessageMapper.to_dto(message)
                return message
            except IntegrityError as e:
                await session.rollback()
                raise ChatNotFound()

    async def read_messages(self, chat_id: int, user_id: int) -> None:
        async with self.get_session() as session:
            await session.execute(
                update(ListingChatMessage)
                .where(
                    ListingChatMessage.chat_id == chat_id,
                    ListingChatMessage.user_id != user_id,
                )
                .values(is_read=True)
            )
            await session.commit()


class ChatRepository(IChatRepository, BaseRepository):

    async def create_chat(self, buyer_id: int, listing_id: int) -> ChatDTO:
        async with self.get_session() as session:
            chat = ListingChat(buyer_id=buyer_id, listing_id=listing_id)
            session.add(chat)
            await session.commit()
            await session.refresh(chat)
            return ChatMapper.to_dto(chat)

    async def get_chat_by_listing_and_buyer(
        self, listing_id: int, buyer_id: int
    ) -> Optional[ChatDTO]:
        async with self.get_session() as session:
            query = select(ListingChat).where(
                ListingChat.listing_id == listing_id, ListingChat.buyer_id == buyer_id
            )
            result = await session.execute(query)
            chat = result.scalar()
            if chat:
                return ChatMapper.to_dto(chat)
            return None

    async def get_chat_by_buyer_and_listing_ids(
        self, buyer_id: int, listing_id: int
    ) -> Optional[ChatDTO]:
        async with self.get_session() as session:
            query = select(ListingChat).filter(
                ListingChat.buyer_id == buyer_id,
                ListingChat.listing_id == listing_id,
            )
            results = await session.execute(query)
            chat = results.scalar()
            if chat:
                return ChatMapper.to_dto(chat)
            return None

    async def get_chat_with_listing_by_id(
        self, chat_id: int
    ) -> Optional[ChatWithListingDTO]:
        async with self.get_session() as session:
            query = (
                select(ListingChat)
                .options(joinedload(ListingChat.listing))
                .where(ListingChat.id == chat_id)
            )
            result = await session.execute(query)
            chat = result.scalar()
            if chat:
                return ChatMapper.to_dto_with_listing(chat)
            return None

    async def get_user_chats(
        self, user_id: int, limit: int, offset: int
    ) -> Tuple[List[ShortChatSchema], int]:
        async with self.get_session() as session:
            # Подзапрос для последнего сообщения
            latest_message_subquery = (
                select(
                    ListingChatMessage.chat_id,
                    ListingChatMessage.created_at.label("last_message_datetime"),
                    ListingChatMessage.message.label("last_message_text"),
                )
                .join(ListingChat, ListingChat.id == ListingChatMessage.chat_id)
                .where(
                    ListingChatMessage.created_at
                    == select(func.max(ListingChatMessage.created_at))
                    .where(ListingChatMessage.chat_id == ListingChat.id)
                    .correlate(ListingChat)
                    .scalar_subquery()
                )
                .subquery()
            )

            # Подзапрос для самой ранней картинки
            earliest_image_subquery = (
                select(
                    Listing.id.label("listing_id"),
                    func.min(ListingImage.created_at).label("earliest_image_datetime"),
                )
                .join(ListingImage, Listing.id == ListingImage.listing_id)
                .group_by(Listing.id)
                .subquery()
            )

            # Подзапрос для непрочитанных сообщений
            unread_messages_subquery = (
                select(
                    ListingChatMessage.chat_id,
                    func.count(ListingChatMessage.id).label("unread_messages_count"),
                )
                .filter(
                    ListingChatMessage.is_read == False,
                    ListingChatMessage.user_id != user_id,
                )
                .group_by(ListingChatMessage.chat_id)
                .subquery()
            )

            # Основной запрос с объединениями и фильтрацией
            query = (
                select(
                    ListingChat,
                    latest_message_subquery.c.last_message_datetime,
                    latest_message_subquery.c.last_message_text,
                    earliest_image_subquery.c.earliest_image_datetime,
                    unread_messages_subquery.c.unread_messages_count,
                )
                .join(listings := Listing, ListingChat.listing_id == listings.id)
                .join(
                    latest_message_subquery,
                    ListingChat.id == latest_message_subquery.c.chat_id,
                    isouter=True,
                )
                .join(
                    earliest_image_subquery,
                    ListingChat.listing_id == earliest_image_subquery.c.listing_id,
                    isouter=True,
                )
                .join(
                    unread_messages_subquery,
                    ListingChat.id == unread_messages_subquery.c.chat_id,
                    isouter=True,
                )
                .filter(
                    or_(ListingChat.buyer_id == user_id, listings.user_id == user_id)
                )
                .options(
                    selectinload(ListingChat.listing).selectinload(Listing.user),
                    selectinload(ListingChat.listing).selectinload(Listing.images),
                    selectinload(ListingChat.buyer),
                )
                .distinct(
                    latest_message_subquery.c.last_message_datetime, ListingChat.id
                )
                .order_by(
                    latest_message_subquery.c.last_message_datetime.desc(),
                    ListingChat.id,
                )
                .limit(limit)
                .offset(offset)
            )

            results = await session.execute(query)
            chats_with_additional_data = results.unique().all()

            # Подсчет общего количества чатов
            count_query = (
                select(func.count(ListingChat.id))
                .join(listings, ListingChat.listing_id == listings.id)
                .filter(
                    or_(ListingChat.buyer_id == user_id, listings.user_id == user_id)
                )
            )
            count_result = await session.execute(count_query)
            count = count_result.scalar()

            # Подсчет количества чатов с непрочитанными сообщениями
            unread_chats_query = (
                select(func.count(distinct(ListingChat.id)))
                .join(ListingChatMessage, ListingChat.id == ListingChatMessage.chat_id)
                .filter(
                    or_(ListingChat.buyer_id == user_id, listings.user_id == user_id),
                    ListingChatMessage.is_read == False,
                    ListingChatMessage.user_id != user_id,
                )
            )
            unread_chats_result = await session.execute(unread_chats_query)
            unread_chats_count = unread_chats_result.scalar()

            # Формирование выходных данных
            chats = [
                (
                    chat,
                    last_message_datetime,
                    last_message_text,
                    earliest_image_datetime,
                    unread_messages_count or 0,
                )
                for chat, last_message_datetime, last_message_text, earliest_image_datetime, unread_messages_count in chats_with_additional_data
            ]

            chat_schemas = ChatMapper.to_short_schema_list(chats, user_id)
            return chat_schemas, count, unread_chats_count

    async def get_user_chat(self, user_id: int, chat_id: int) -> ShortChatSchema:
        async with self.get_session() as session:

            latest_message_subquery = (
                select(
                    ListingChatMessage.chat_id,
                    ListingChatMessage.created_at.label("last_message_datetime"),
                    ListingChatMessage.message.label("last_message_text"),
                )
                .where(ListingChatMessage.chat_id == chat_id)
                .order_by(ListingChatMessage.created_at.desc())
                .limit(1)
                .subquery()
            )

            # Подзапрос для самой ранней картинки
            earliest_image_subquery = (
                select(
                    Listing.id.label("listing_id"),
                    func.min(ListingImage.created_at).label("earliest_image_datetime"),
                )
                .join(ListingImage, Listing.id == ListingImage.listing_id)
                .where(Listing.id == ListingChat.listing_id)
                .group_by(Listing.id)
                .subquery()
            )

            # Подзапрос для непрочитанных сообщений
            unread_messages_subquery = (
                select(
                    ListingChatMessage.chat_id,
                    func.count(ListingChatMessage.id).label("unread_messages_count"),
                )
                .where(
                    ListingChatMessage.chat_id == chat_id,
                    ListingChatMessage.is_read == False,
                    ListingChatMessage.user_id != user_id,
                )
                .group_by(ListingChatMessage.chat_id)
                .subquery()
            )

            # Основной запрос
            query = (
                select(
                    ListingChat,
                    latest_message_subquery.c.last_message_datetime,
                    latest_message_subquery.c.last_message_text,
                    earliest_image_subquery.c.earliest_image_datetime,
                    unread_messages_subquery.c.unread_messages_count,
                )
                .join(Listing, ListingChat.listing_id == Listing.id)
                .join(
                    latest_message_subquery,
                    ListingChat.id == latest_message_subquery.c.chat_id,
                    isouter=True,
                )
                .join(
                    earliest_image_subquery,
                    ListingChat.listing_id == earliest_image_subquery.c.listing_id,
                    isouter=True,
                )
                .join(
                    unread_messages_subquery,
                    ListingChat.id == unread_messages_subquery.c.chat_id,
                    isouter=True,
                )
                .where(
                    ListingChat.id == chat_id,
                    or_(ListingChat.buyer_id == user_id, Listing.user_id == user_id),
                )
                .options(
                    joinedload(ListingChat.listing).joinedload(Listing.user),
                    joinedload(ListingChat.listing).joinedload(Listing.images),
                    joinedload(ListingChat.buyer),
                )
            )

            result = await session.execute(query)
            chat_with_additional_data = result.unique().first()

            if not chat_with_additional_data:
                raise ChatNotFound()

            # Формирование выходных данных
            (
                chat,
                last_message_datetime,
                last_message_text,
                earliest_image_datetime,
                unread_messages_count,
            ) = chat_with_additional_data

            chat_schema = ChatMapper.to_short_schema(
                chat,
                user_id,
                last_message_datetime,
                last_message_text,
                earliest_image_datetime,
                unread_messages_count or 0,
            )
            return chat_schema


class ChatAggregateRepository(IChatAggregateRepository, BaseRepository):

    async def get_detail_chat_by_id(
        self, chat_id: int, user_id: int, limit: int, offset: int
    ) -> Optional[DetailChatSchema]:
        async with self.get_session() as session:
            earliest_image_subquery = (
                select(
                    Listing.id.label("listing_id"),
                    func.min(ListingImage.created_at).label("earliest_image_datetime"),
                )
                .join(ListingImage, Listing.id == ListingImage.listing_id)
                .group_by(Listing.id)
                .subquery()
            )

            query = (
                select(ListingChat, earliest_image_subquery.c.earliest_image_datetime)
                .options(
                    joinedload(ListingChat.listing).joinedload(Listing.user),
                    joinedload(ListingChat.buyer),
                    joinedload(ListingChat.listing).joinedload(Listing.images),
                )
                .outerjoin(
                    earliest_image_subquery,
                    ListingChat.listing_id == earliest_image_subquery.c.listing_id,
                )
                .filter(
                    ListingChat.id == chat_id,
                    (ListingChat.buyer_id == user_id) | (Listing.user_id == user_id),
                )
            )

            result = await session.execute(query)
            chat_with_additional_data = result.first()

            if not chat_with_additional_data:
                return None

            chat, earliest_image_datetime = chat_with_additional_data

            messages_query = (
                select(ListingChatMessage)
                .filter(ListingChatMessage.chat_id == chat_id)
                .order_by(ListingChatMessage.created_at)
                .limit(limit)
                .offset(offset)
            )

            messages_result = await session.execute(messages_query)
            messages = messages_result.scalars().all()
            count_query = select(func.count(ListingChatMessage.id)).filter(
                ListingChatMessage.chat_id == chat_id
            )

            count_result = await session.execute(count_query)
            total_count = count_result.scalar()

            detail_chat_schema = ChatMapper.to_detail_schema(
                chat, earliest_image_datetime, messages, total_count, user_id
            )

            return detail_chat_schema
