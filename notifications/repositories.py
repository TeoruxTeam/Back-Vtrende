from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from sqlalchemy import delete, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.repositories import BaseRepository
from users.schemas import UserDTO

from .mappers import FCMTokenMapper, NotificationMapper, NotificationSettingsMapper
from .models import FCMToken, Notification, NotificationSettings
from .schemas import (
    FCMTokenFromORM,
    FCMTokenSchema,
    NotificationFromORM,
    NotificationSchema,
    NotificationSettingsFromORM,
    PutNotificationSettingsRequest,
)


class INotificationRepository(ABC):

    @abstractmethod
    async def add_notification(
        self, notification: NotificationSchema, external_session: Optional[AsyncSession]
    ) -> None:
        pass

    @abstractmethod
    async def get_notifications_by_user_id(
        self, user_id: int, limit: int, offset: int, include_read: bool
    ) -> Tuple[List[NotificationFromORM], int]:
        pass

    @abstractmethod
    async def read_notifications_by_ids(
        self, notification_ids: List[int], user_id: int
    ) -> None:
        pass


class NotificationRepository(INotificationRepository, BaseRepository):

    async def add_notification(
        self, notification: NotificationSchema, external_session: Optional[AsyncSession]
    ) -> None:
        async with self.get_session(external_session) as session:
            notification_entity = NotificationMapper.from_schema_to_entity(notification)
            session.add(notification_entity)

            if not external_session:
                await session.commit()

    async def get_notifications_by_user_id(
        self, user_id: int, limit: int, offset: int, include_read: bool
    ) -> Tuple[List[NotificationFromORM], int]:
        async with self.get_session() as session:
            query = select(Notification).where(Notification.user_id == user_id)
            count_query = select(func.count(Notification.id)).where(
                Notification.user_id == user_id
            )

            if not include_read:
                query = query.where(Notification.is_read == False)
                count_query = count_query.where(Notification.is_read == False)

            query = query.limit(limit).offset(offset)
            results = await session.execute(query)
            notifications = results.scalars().all()
            notifications = [
                NotificationMapper.from_orm(notification)
                for notification in notifications
            ]

            count_result = await session.execute(count_query)
            count = count_result.scalar()

            return notifications, count

    async def read_notifications_by_ids(
        self, notification_ids: List[int], user_id: int
    ) -> None:
        async with self.get_session() as session:
            await session.execute(
                update(Notification)
                .where(
                    Notification.id.in_(notification_ids),
                    Notification.user_id == user_id,
                )
                .values(is_read=True)
            )
            await session.commit()


class IFCMTokenRepository(ABC):

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
    async def delete_fcm_tokens_by_tokens(self, tokens: List[str]) -> None:
        pass


class FCMTokenRepository(IFCMTokenRepository, BaseRepository):

    async def add_fcm_token(self, token_data: FCMTokenSchema, user_id: int) -> None:
        async with self.get_session() as session:
            new_token = FCMToken(
                user_id=user_id,
                fcm_token=token_data.fcm_token,
                device_id=token_data.device_id,
            )
            session.add(new_token)
            await session.commit()

    async def get_fcm_token_by_device_id(self, device_id: str) -> FCMTokenFromORM:
        async with self.get_session() as session:
            results = await session.execute(
                select(FCMToken).where(FCMToken.device_id == device_id)
            )
            token = results.scalar()
            return FCMTokenMapper.to_schema_from_orm(token) if token else None

    async def update_fcm_token_by_id(self, token_id: int, fcm_token: str) -> None:
        async with self.get_session() as session:
            await session.execute(
                update(FCMToken)
                .where(FCMToken.id == token_id)
                .values(fcm_token=fcm_token)
            )
            await session.commit()

    async def delete_fcm_token_by_device_id(self, device_id: str, user_id: int) -> None:
        async with self.get_session() as session:
            await session.execute(
                delete(FCMToken).where(
                    FCMToken.device_id == device_id, FCMToken.user_id == user_id
                )
            )
            await session.commit()

    async def get_frm_tokens_by_user_ids(
        self, user_ids: List[int]
    ) -> List[FCMTokenFromORM]:
        async with self.get_session() as session:
            result = await session.execute(
                select(FCMToken).where(FCMToken.user_id.in_(user_ids))
            )
            tokens = result.scalars().all()

            user_token_pairs = [
                FCMTokenMapper.to_schema_from_orm(token) for token in tokens
            ]

            return user_token_pairs

    async def delete_fcm_tokens_by_tokens(self, tokens: List[str]) -> None:
        async with self.get_session() as session:
            await session.execute(
                delete(FCMToken).where(FCMToken.fcm_token.in_(tokens))
            )
            await session.commit()


class INotificationSettingsRepository(ABC):

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


class NotificationSettingsRepository(INotificationSettingsRepository, BaseRepository):

    async def get_notification_settings_by_user_id(
        self, user_id: int
    ) -> NotificationSettingsFromORM:
        async with self.get_session() as session:
            result = await session.execute(
                select(NotificationSettings).where(
                    NotificationSettings.user_id == user_id
                )
            )
            settings = result.scalar()
            return (
                NotificationSettingsMapper.to_schema_from_orm(settings)
                if settings
                else None
            )

    async def update_notification_settings(
        self, user_id: int, settings: PutNotificationSettingsRequest
    ) -> None:
        async with self.get_session() as session:
            await session.execute(
                update(NotificationSettings)
                .where(NotificationSettings.user_id == user_id)
                .values(
                    notify_new_messages=settings.notify_new_messages,
                    notify_recommendations=settings.notify_recommendations,
                )
            )
            await session.commit()

    async def get_users_with_disabled_listing_notifications(
        self, user_ids: List[int]
    ) -> List[int]:
        async with self.get_session() as session:
            result = await session.execute(
                select(NotificationSettings).where(
                    NotificationSettings.user_id.in_(user_ids),
                    NotificationSettings.notify_recommendations == False,
                )
            )
            settings = result.scalars().all()
            return [
                NotificationSettingsMapper.to_schema_from_orm(setting)
                for setting in settings
            ]
