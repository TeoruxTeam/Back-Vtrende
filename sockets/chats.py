from typing import List

import socketio
from dependency_injector.wiring import Provide, inject
from sqlalchemy.exc import IntegrityError

from chats.exceptions import ChatNotFound
from chats.facade import IChatFacade
from chats.schemas import (
    ChatMessageDTO,
    ChatWithListingDTO,
    CreateChatAndMessageRequestSchema,
    CreateMessageRequestSchema,
    ShortChatSchema,
)
from core.container import Container
from core.logger import logger
from core.redis_client import RedisPool
from core.socketio_server import CustomSocketServer
from core.tasks import send_notifications
from core.utils import serialize_datetime
from listings.exceptions import ListingNotFound
from listings.facade import IListingFacade
from notifications.facade import INotificationFacade
from notifications.schemas import NotificationSchema


@inject
def setup_chat_handlers(
    sio: CustomSocketServer,
    chat_facade: IChatFacade = Provide[Container.chat_facade],
    listing_facade: IListingFacade = Provide[Container.listing_facade],
    redis_pool: RedisPool = Provide[Container.redis_pool],
):
    @sio.on("create_chat_and_first_message")
    async def create_chat_and_first_message(sid, data):
        schema = sio.validate_request(data, CreateChatAndMessageRequestSchema)
        if not schema:
            await sio.emit(
                "validation_error", {"detail": "error.body.invalid.schema"}, room=sid
            )

        async with redis_pool.get_redis() as redis_manager:
            user_id = await redis_manager.get(f"sid:{sid}")
            user_id = int(user_id.decode("utf-8"))
            if user_id:
                try:
                    listing = await listing_facade.get_short_listing_by_id(
                        schema.listing_id
                    )
                    if listing.user_id == user_id:
                        await sio.emit(
                            "error", {"error": "error.chat.your_own_listing"}, room=sid
                        )
                        return
                    chat = await chat_facade.create_chat(user_id, listing.id)
                except IntegrityError:
                    await sio.emit(
                        "error", {"error": "error.chat.already.exists"}, room=sid
                    )
                    return
                except ListingNotFound:
                    await sio.emit(
                        "error", {"error": "error.listing.not_found"}, room=sid
                    )
                    return

                message = await chat_facade.create_message(
                    chat.id, user_id, schema.message
                )
                short_chat_schema_sender = (
                    await chat_facade.get_short_chat_data_by_id_and_user_id(
                        chat.id, user_id
                    )
                )
                short_chat_schema_recipient = (
                    await chat_facade.get_short_chat_data_by_id_and_user_id(
                        chat.id, listing.user_id
                    )
                )

                sender_sessions = await redis_manager.smembers(
                    f"user_sessions:{user_id}"
                )
                sender_sessions = [s.decode("utf-8") for s in sender_sessions]
                recipient_sessions = await redis_manager.smembers(
                    f"user_sessions:{listing.user_id}"
                )
                recipient_sessions = [s.decode("utf-8") for s in recipient_sessions]

                sender_username = await redis_manager.get(f"user_username:{user_id}")
                sender_username = (
                    sender_username.decode("utf-8") if sender_username else "undefined"
                )
                logger.warning(
                    f"Current sid {sid}, sesssions {sender_sessions}, {recipient_sessions}"
                )
                await sio.emit_to_sessions(
                    sender_sessions,
                    "new_chat",
                    serialize_datetime(short_chat_schema_sender.dict()),
                )
                await sio.emit_to_sessions(
                    recipient_sessions,
                    "new_chat",
                    serialize_datetime(short_chat_schema_recipient.dict()),
                )

                await sio.emit_to_sessions(
                    sender_sessions,
                    "new_message",
                    {"chat_id": chat.id, "message": message.dict()},
                )
                await sio.emit_to_sessions(
                    recipient_sessions,
                    "new_message",
                    {"chat_id": chat.id, "message": message.dict()},
                )

                notifications = [
                    {
                        "user_id": listing.user_id,
                        "message": f"notifications.chats.new_message.user.{user_id}.{sender_username}.chat.{chat.id}",
                    }
                ]
                send_notifications.delay(notifications)
            else:
                logger.warning(f"No user associated with sid: {sid}")
                await sio.emit(
                    "auth_error", {"error": "User not authenticated"}, room=sid
                )

    @sio.on("create_message")
    async def create_message(sid, data):
        schema = sio.validate_request(data, CreateMessageRequestSchema)
        if not schema:
            await sio.emit("validation_error", {"detail": "error.body.invalid.schema"})

        async with redis_pool.get_redis() as redis_manager:
            user_id = await redis_manager.get(f"sid:{sid}")
            user_id = int(user_id.decode("utf-8"))
            if user_id:
                try:
                    logger.info(f"Getting chat {schema.chat_id}")
                    chat: ChatWithListingDTO = (
                        await chat_facade.get_chat_with_listing_by_id(schema.chat_id)
                    )
                    logger.info(f"Chat {chat}")
                    message: ChatMessageDTO = await chat_facade.create_message(
                        schema.chat_id, user_id, schema.message
                    )
                except ChatNotFound:
                    await sio.emit("error", {"error": "error.chat.not_found"})
                    return

                sender_sessions = await redis_manager.smembers(
                    f"user_sessions:{user_id}"
                )
                sender_sessions = [s.decode("utf-8") for s in sender_sessions]
                recipient_id = (
                    chat.buyer_id if chat.buyer_id != user_id else chat.listing.user_id
                )
                recipient_sessions = await redis_manager.smembers(
                    f"user_sessions:{recipient_id}"
                )
                recipient_sessions = [s.decode("utf-8") for s in recipient_sessions]

                sender_username = await redis_manager.get(f"user_username:{user_id}")
                sender_username = (
                    sender_username.decode("utf-8") if sender_username else "undefined"
                )

                logger.warning(f"sender_sessions:{sender_sessions}")
                logger.warning(f"recipient_sessions:{recipient_sessions}")
                message = message.dict()
                logger.warning(
                    f"Current sid {sid}, sesssions {sender_sessions}, {recipient_sessions}"
                )
                await sio.emit_to_sessions(
                    sender_sessions,
                    "new_message",
                    {"chat_id": schema.chat_id, "message": message},
                )
                await sio.emit_to_sessions(
                    recipient_sessions,
                    "new_message",
                    {"chat_id": schema.chat_id, "message": message},
                )
                notifications = [
                    {
                        "user_id": recipient_id,
                        "message": f"notifications.chats.new_message.user.{user_id}.{sender_username}.chat.{chat.id}",
                    }
                ]
                send_notifications.delay(notifications)
            else:
                logger.warning(f"No user associated with sid: {sid}")
                await sio.emit(
                    "auth_error", {"error": "User not authenticated"}, room=sid
                )
