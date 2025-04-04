from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from core.utils import get_media_url

from .exceptions import ChatNotFound
from .repositories import IChatAggregateRepository, IChatRepository, IMessageRepository
from .schemas import (
    ChatDTO,
    ChatMessageDTO,
    ChatWithListingDTO,
    DetailChatSchema,
    ShortChatSchema,
)


class IMessageService(ABC):
    @abstractmethod
    async def get_messages(self, chat_id: int):
        pass

    @abstractmethod
    async def create_message(
        self, chat_id: int, user_id: int, message: str
    ) -> Optional[ChatMessageDTO]:
        pass

    @abstractmethod
    async def read_messages(self, chat_id: int, user_id: int) -> None:
        pass


class IChatService(ABC):
    @abstractmethod
    async def get_chats(self, user_id: int):
        pass

    @abstractmethod
    async def create_chat(self, buyer_id: int, listing_id: int):
        pass

    @abstractmethod
    async def get_chat_by_listing_and_buyer(self, listing_id: int, buyer_id: int):
        pass

    @abstractmethod
    async def get_chat_by_users(
        self, buyer_id: int, listing_id: int
    ) -> Optional[ChatDTO]:
        pass

    @abstractmethod
    async def get_chat_with_listing_by_id(self, chat_id: int) -> ChatWithListingDTO:
        pass

    @abstractmethod
    async def get_user_chat(self, user_id: int, chat_id: int) -> ShortChatSchema:
        pass

    @abstractmethod
    async def get_user_chats(
        self, user_id: int, limit: int, offset: int, base_url: str
    ) -> Tuple[List[ShortChatSchema], int, int]:
        pass


class IChatAggregateService(ABC):
    @abstractmethod
    async def get_detail_chat_by_id(
        self, chat_id: int, user_id: int, base_url: int, limit: int, offset: int
    ) -> DetailChatSchema:
        pass


class MessageService(IMessageService):
    def __init__(self, repo: IMessageRepository):
        self.repo = repo

    async def get_messages(self, chat_id: int):
        messages = await self.repo.get_messages(chat_id)
        return messages

    async def create_message(
        self, chat_id: int, user_id: int, message: str
    ) -> ChatMessageDTO:
        return await self.repo.create_message(chat_id, user_id, message)

    async def read_messages(self, chat_id: int, user_id: int) -> None:
        return await self.repo.read_messages(chat_id, user_id)


class ChatService(IChatService):
    def __init__(self, repo: IChatRepository):
        self.repo = repo

    async def get_chats(self, user_id: int):
        chats = await self.repo.get_chats(user_id)
        return chats

    async def create_chat(self, buyer_id: int, listing_id: int) -> ChatDTO:
        return await self.repo.create_chat(buyer_id, listing_id)

    async def get_chat_by_listing_and_buyer(self, listing_id: int, buyer_id: int):
        chat = await self.repo.get_chat_by_listing_and_buyer(listing_id, buyer_id)
        return chat

    async def get_chat_by_users(
        self, buyer_id: int, listing_id: int
    ) -> Optional[ChatDTO]:
        return await self.repo.get_chat_by_buyer_and_listing_ids(
            buyer_id=buyer_id, listing_id=listing_id
        )

    async def get_chat_with_listing_by_id(
        self, chat_id: int
    ) -> Optional[ChatWithListingDTO]:
        return await self.repo.get_chat_with_listing_by_id(chat_id)

    async def get_user_chats(
        self, user_id: int, limit: int, offset: int, base_url: str
    ) -> Tuple[List[ShortChatSchema], int]:
        chats, count, unread_messages_count = await self.repo.get_user_chats(
            user_id, limit, offset
        )
        for chat in chats:
            chat.listing_photo = get_media_url(base_url, chat.listing_photo)
            chat.interlocutor_avatar = get_media_url(base_url, chat.interlocutor_avatar)
        return chats, count, unread_messages_count

    async def get_user_chat(self, user_id: int, chat_id: int) -> ShortChatSchema:
        return await self.repo.get_user_chat(user_id, chat_id)


class ChatAggregateService(IChatAggregateService):
    def __init__(self, repo: IChatAggregateRepository):
        self.repo = repo

    async def get_detail_chat_by_id(
        self, chat_id: int, user_id: int, base_url: int, limit: int, offset: int
    ) -> DetailChatSchema:
        chat: DetailChatSchema = await self.repo.get_detail_chat_by_id(
            chat_id, user_id, limit, offset
        )
        if not chat:
            raise ChatNotFound()
        chat.interlocutor_avatar = get_media_url(base_url, chat.interlocutor_avatar)
        chat.listing_photo = get_media_url(base_url, chat.listing_photo)
        return chat
