import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

from dependency_injector.wiring import Provide, inject
from firebase_admin import messaging
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from core.redis_client import RedisPool
from core.socketio_server import CustomSocketServer
from users.schemas import UserDTO

from .repositories import (
    IFCMTokenRepository,
    INotificationRepository,
    INotificationSettingsRepository,
)
from .schemas import (
    FCMTokenFromORM,
    FCMTokenSchema,
    NotificationFromORM,
    NotificationSchema,
    NotificationSettingsFromORM,
    PutNotificationSettingsRequest,
)


class INotificationService(ABC):

    @abstractmethod
    async def listen_for_notifications(
        self, sio: CustomSocketServer, user_id: int, redis_pool: RedisPool
    ):
        pass

    @abstractmethod
    async def notify_users(
        self, notifications: List[NotificationSchema], redis_pool: RedisPool
    ):
        pass

    @abstractmethod
    async def create_notification(
        self, notification: NotificationSchema, session: Optional[AsyncSession] = None
    ):
        pass

    @abstractmethod
    def send_fcm_notifications(
        self, token_message_pairs: List[Dict[str, str]]
    ) -> List[str]:
        pass

    @abstractmethod
    async def get_notifications_by_user_id(
        self, user_id: int, limit: int, offset: int, include_read: bool
    ) -> Tuple[List[NotificationFromORM], int]:
        pass

    @abstractmethod
    async def read_notifications_by_ids(
        self, notification_ids: List[int], user_id: List[int]
    ) -> None:
        pass


class NotificationService(INotificationService):

    def __init__(self, repo: INotificationRepository):
        self.repo = repo

    def send_fcm_notifications(
        self, token_message_pairs: List[Dict[str, str]]
    ) -> List[str]:
        """
        Sends notifications via FCM with unique messages for each token.
        Returns a list of invalid tokens.
        """
        invalid_tokens = []

        for pair in token_message_pairs:
            try:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title="Notification",
                        body=pair["message"],
                    ),
                    token=pair["token"],
                )
                response = messaging.send(message)
                logger.info(f"Message sent successfully to token: {pair['token']}")
            except messaging.FirebaseError as e:
                logger.error(
                    f"Failed to send message to token: {pair['token']}. Error: {e}"
                )
                if "invalid" in str(e).lower():
                    invalid_tokens.append(pair["token"])

        if invalid_tokens:
            logger.info(f"Invalid tokens identified: {invalid_tokens}")

        return invalid_tokens

    async def listen_for_notifications(
        self, sio: CustomSocketServer, user_id: int, redis_pool: RedisPool
    ):
        async with redis_pool.get_redis() as redis:
            last_id = "0"

            while True:
                messages = await redis.xread(
                    [f"user_notifications:{user_id}"],
                    count=10,
                    block=5000,
                    latest_ids=[last_id],
                )
                for stream, msgs in messages:
                    for msg_id, msg_data in msgs:
                        message = msg_data["message"].decode("utf-8")
                        user_sessions = await redis.smembers(f"user_sessions:{user_id}")

                        undelivered_sessions = []
                        for session_id in user_sessions:
                            attempts = 0
                            success = False

                            while attempts < 3:
                                try:
                                    await sio.emit(
                                        "notification",
                                        message,
                                        room=session_id.decode("utf-8"),
                                    )
                                    success = True
                                    break
                                except Exception as e:
                                    attempts += 1
                                    await asyncio.sleep(20)

                            if not success:
                                undelivered_sessions.append(session_id)

                        if undelivered_sessions:
                            print(
                                f"Не доставлено уведомление для сессий после 3 попыток: {undelivered_sessions}"
                            )
                        else:
                            await redis.xack(
                                f"user_notifications:{user_id}", "group", msg_id
                            )
                            await redis.xdel(f"user_notifications:{user_id}", msg_id)

                await asyncio.sleep(1)

    async def notify_users(
        self, notifications: List[NotificationSchema], redis_pool: RedisPool
    ):
        """
        Добавляет уведомления в Redis Stream для каждого пользователя в списке notifications.
        """
        async with redis_pool.get_redis() as redis:
            for notification in notifications:
                await redis.xadd(
                    f"user_notifications:{notification.user_id}",
                    {"message": notification.message},
                    maxlen=1000,
                    approximate=True,
                )

    async def create_notification(
        self, notification: NotificationSchema, session: Optional[AsyncSession] = None
    ):
        """
        Добавляет уведомление в базу данных
        """
        await self.repo.add_notification(notification, session)

    async def get_notifications_by_user_id(
        self, user_id: int, limit: int, offset: int, include_read: bool
    ) -> Tuple[List[NotificationFromORM], int]:
        return await self.repo.get_notifications_by_user_id(
            user_id, limit, offset, include_read
        )

    async def read_notifications_by_ids(
        self, notification_ids: List[int], user_id: List[int]
    ) -> None:
        await self.repo.read_notifications_by_ids(notification_ids, user_id)


class IFCMTokenService(ABC):

    @abstractmethod
    async def add_fcm_token(self, token_data: FCMTokenSchema, user_id: int) -> None:
        pass

    @abstractmethod
    async def get_fcm_token_by_device_id(self, device_id: str) -> FCMTokenFromORM:
        pass

    @abstractmethod
    async def update_fcm_token_by_id(self, token_id: int, fcm_token: str) -> None:
        pass

    @abstractmethod
    async def delete_fcm_token_by_device_id(self, device_id: str, user_id: int) -> None:
        pass

    @abstractmethod
    async def get_frm_tokens_by_user_ids(
        self, user_ids: List[int]
    ) -> List[FCMTokenFromORM]:
        pass

    @abstractmethod
    async def delete_tokens_by_tokens(self, tokens: List[str]) -> None:
        pass


class FCMTokenService(IFCMTokenService):

    def __init__(self, repo: IFCMTokenRepository):
        self.repo = repo

    async def add_fcm_token(self, token_data: FCMTokenSchema, user_id: int) -> None:
        await self.repo.add_fcm_token(token_data, user_id)

    async def get_fcm_token_by_device_id(self, device_id: str) -> FCMTokenFromORM:
        return await self.repo.get_fcm_token_by_device_id(device_id)

    async def update_fcm_token_by_id(self, token_id: int, fcm_token: str) -> None:
        await self.repo.update_fcm_token_by_id(token_id, fcm_token)

    async def delete_fcm_token_by_device_id(self, device_id: str, user_id: int) -> None:
        await self.repo.delete_fcm_token_by_device_id(device_id, user_id)

    async def get_frm_tokens_by_user_ids(
        self, user_ids: List[int]
    ) -> List[FCMTokenFromORM]:
        return await self.repo.get_frm_tokens_by_user_ids(user_ids)

    async def delete_tokens_by_tokens(self, tokens: List[str]) -> None:
        return await self.repo.delete_fcm_tokens_by_tokens(tokens)


class INotificationSettingsService(ABC):

    @abstractmethod
    async def get_notification_settings_by_user_id(
        self, user_id: int
    ) -> NotificationSettingsFromORM:
        pass

    @abstractmethod
    async def update_notification_settings(
        self, user_id: int, settings: PutNotificationSettingsRequest
    ) -> None:
        pass

    @abstractmethod
    async def get_users_with_disabled_listing_notifications(
        self, user_ids: List[int]
    ) -> List[int]:
        pass


class NotificationSettingsService(INotificationSettingsService):

    def __init__(self, repo: INotificationSettingsRepository):
        self.repo = repo

    async def get_notification_settings_by_user_id(
        self, user_id: int
    ) -> NotificationSettingsFromORM:
        return await self.repo.get_notification_settings_by_user_id(user_id)

    async def update_notification_settings(
        self, user_id: int, settings: PutNotificationSettingsRequest
    ) -> None:
        await self.repo.update_notification_settings(user_id, settings)

    async def get_users_with_disabled_listing_notifications(
        self, user_ids: List[int]
    ) -> List[int]:
        return await self.repo.get_users_with_disabled_listing_notifications(user_ids)
