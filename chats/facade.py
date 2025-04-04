from abc import ABC, abstractmethod
from typing import List, Optional

from users.schemas import UserDTO

from .exceptions import ChatNotFound
from .schemas import (
    ChatDTO,
    ChatMessageDTO,
    ChatWithListingDTO,
    GetChatListResponseSchema,
    GetDetailChatResponseSchema,
    GetListingChatResponseSchema,
    ReadChatResponseSchema,
    ShortChatSchema,
)
from .services import IChatAggregateService, IChatService, IMessageService


class IChatFacade(ABC):

    @abstractmethod
    async def create_chat(self, buyer_id: int, listing_id: int) -> ChatDTO:
        pass

    @abstractmethod
    async def create_message(self, chat_id: int, user_id: int, message: str):
        pass

    @abstractmethod
    async def get_chat_with_listing_by_id(
        self, chat_id: int
    ) -> Optional[ChatWithListingDTO]:
        pass

    @abstractmethod
    async def get_user_chats(
        self, user_id: int, limit: int, offset: int, base_url: str
    ) -> GetChatListResponseSchema:
        pass

    @abstractmethod
    async def get_short_chat_data_by_id_and_user_id(
        self, chat_id: int, user_id: int
    ) -> ShortChatSchema:
        pass

    @abstractmethod
    async def get_short_listing_chat_as_buyer(
        self, listing_id: int, user_id: int
    ) -> GetListingChatResponseSchema:
        pass

    @abstractmethod
    async def get_detail_chat(
        self,
        chat_id: int,
        user_id: int,
        base_url: int,
        limit: int,
        offset: int,
    ) -> GetDetailChatResponseSchema:
        pass

    @abstractmethod
    async def read_chat(
        self,
        chat_id: int,
        user_id: int,
    ) -> ReadChatResponseSchema:
        pass


class ChatFacade(IChatFacade):
    def __init__(
        self,
        chat_service: IChatService,
        message_service: IMessageService,
        chat_aggregate_service: IChatAggregateService,
    ):
        self.chat_service = chat_service
        self.message_service = message_service
        self.chat_aggregate_service = chat_aggregate_service

    async def create_chat(self, buyer_id: int, listing_id: int) -> ChatDTO:
        return await self.chat_service.create_chat(buyer_id, listing_id)

    async def create_message(
        self, chat_id: int, user_id: int, message: str
    ) -> ChatMessageDTO:
        return await self.message_service.create_message(chat_id, user_id, message)

    async def get_chat_with_listing_by_id(
        self, chat_id: int
    ) -> Optional[ChatWithListingDTO]:
        return await self.chat_service.get_chat_with_listing_by_id(chat_id)

    async def get_user_chats(
        self, user_id: int, limit: int, offset: int, base_url: str
    ) -> GetChatListResponseSchema:
        chats, count, unread_messages_count = await self.chat_service.get_user_chats(
            user_id, limit, offset, base_url
        )
        return GetChatListResponseSchema(
            count=count, data=chats, unread_messages_count=unread_messages_count
        )

    async def get_short_listing_chat_as_buyer(
        self, listing_id: int, user_id: int
    ) -> GetListingChatResponseSchema:
        chat = await self.chat_service.get_chat_by_listing_and_buyer(
            listing_id, user_id
        )
        if not chat:
            raise ChatNotFound()
        return GetListingChatResponseSchema(data=chat)

    async def get_detail_chat(
        self, chat_id: int, user_id: int, base_url: int, limit: int, offset: int
    ) -> GetDetailChatResponseSchema:
        chat = await self.chat_aggregate_service.get_detail_chat_by_id(
            chat_id, user_id, base_url, limit, offset
        )
        return GetDetailChatResponseSchema(data=chat)

    async def read_chat(
        self,
        chat_id: int,
        user_id: int,
    ) -> ReadChatResponseSchema:
        chat: ChatWithListingDTO = await self.chat_service.get_chat_with_listing_by_id(
            chat_id
        )
        if user_id != chat.buyer_id and user_id != chat.listing.user_id:
            raise ChatNotFound()
        await self.message_service.read_messages(chat_id, user_id)
        return ReadChatResponseSchema()

    async def get_short_chat_data_by_id_and_user_id(
        self, chat_id: int, user_id: int
    ) -> ShortChatSchema:
        return await self.chat_service.get_user_chat(user_id, chat_id)
