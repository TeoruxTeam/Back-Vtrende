from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel

from core.schemas import CountSchema, StatusOkSchema
from listings.schemas import ListingDTO


class CreateChatAndMessageRequestSchema(BaseModel):
    message: str
    listing_id: int


class CreateMessageRequestSchema(BaseModel):
    message: str
    chat_id: int


class ChatMessageDTO(BaseModel):
    id: int
    chat_id: int
    user_id: int
    message: str
    created_at: datetime

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        data["created_at"] = data["created_at"].isoformat()
        return data


class ChatDTO(BaseModel):
    id: int
    listing_id: int
    buyer_id: int
    created_at: datetime


class ChatWithListingDTO(ChatDTO):
    listing: ListingDTO


class GetListingChatResponseSchema(StatusOkSchema):
    data: ChatDTO


class BaseChatSchema(BaseModel):
    id: int
    interlocutor_id: int
    interlocutor_name: str
    interlocutor_avatar: Optional[str]
    listing_id: int
    listing_name: str
    listing_photo: Optional[str]
    listing_price: int
    last_message_text: Optional[str]
    last_message_created_at: Optional[datetime]


class ShortChatSchema(BaseChatSchema):
    unread_messages_count: int


class DetailChatSchema(BaseChatSchema, CountSchema):
    messages: List[ChatMessageDTO]


class GetChatListResponseSchema(StatusOkSchema, CountSchema):
    data: List[ShortChatSchema]
    unread_messages_count: int


class GetDetailChatResponseSchema(StatusOkSchema):
    data: DetailChatSchema


class ReadChatResponseSchema(StatusOkSchema):
    message: str = "success.chat.messages.read"
