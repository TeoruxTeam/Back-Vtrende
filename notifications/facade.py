from abc import ABC, abstractmethod
from typing import Dict, List

from core.database import IUnitOfWork
from core.email_sender import EmailSender
from core.logger import logger
from core.redis_client import RedisPool
from core.socketio_server import CustomSocketServer
from items.schemas import ListingDTO
from recommendations.schemas import UserView
from recommendations.services import ICategoryViewService, ISubcategoryViewService
from users.schemas import UserDTO

from .exceptions import FCMTokenNotFound
from .schemas import (
    AddFCMTokenResponse,
    FCMTokenFromORM,
    FCMTokenSchema,
    GetNotificationSettingsResponse,
    GetNotificationsResponse,
    NotificationSchema,
    NotificationSettingsFromORM,
    PutNotificationSettingsRequest,
    PutNotificationSettingsResponse,
    ReadNotificationsRequest,
    ReadNotificationsResponse,
)
from .services import (
    IFCMTokenService,
    INotificationService,
    INotificationSettingsService,
)


class INotificationFacade(ABC):

    @abstractmethod
    async def listen_for_notifications(
        self, sio: CustomSocketServer, user_id: int, redis_pool: RedisPool
    ) -> None:
        pass

    @abstractmethod
    async def notify_new_listing(self, listing: ListingDTO) -> None:
        pass

    @abstractmethod
    async def make_notifications(self, notifications: List[NotificationSchema]) -> None:
        pass

    @abstractmethod
    async def add_fcm_token(
        self, token_data: FCMTokenSchema, user: UserDTO
    ) -> AddFCMTokenResponse:
        pass

    @abstractmethod
    async def delete_fcm_token(self, device_id: str, user: UserDTO) -> None:
        pass

    @abstractmethod
    async def get_notifications(
        self, current_user: UserDTO, limit: int, offset: int, include_read: bool
    ) -> GetNotificationsResponse:
        pass

    @abstractmethod
    async def read_notifications(
        self, payload: ReadNotificationsRequest, user: UserDTO
    ) -> ReadNotificationsResponse:
        pass

    @abstractmethod
    async def get_notification_settings(
        self, user: UserDTO
    ) -> GetNotificationSettingsResponse:
        pass

    @abstractmethod
    async def update_notification_settings(
        self, payload: PutNotificationSettingsRequest, user: UserDTO
    ) -> PutNotificationSettingsResponse:
        pass


class NotificationFacade(INotificationFacade):

    def __init__(
        self,
        notification_service: INotificationService,
        category_view_service: ICategoryViewService,
        subcategory_view_service: ISubcategoryViewService,
        uow: IUnitOfWork,
        fcm_token_service: IFCMTokenService,
        notification_settings_service: INotificationSettingsService,
        email_sender: EmailSender,
        redis_pool: RedisPool,
    ):
        self.notification_service = notification_service
        self.category_view_service = category_view_service
        self.subcategory_view_service = subcategory_view_service
        self.uow = uow
        self.fcm_token_service = fcm_token_service
        self.notification_settings_service = notification_settings_service
        self.email_sender = email_sender
        self.redis_pool = redis_pool

    def _create_token_message_pairs(
        self, tokens: List[FCMTokenFromORM], notifications: List[NotificationSchema]
    ) -> List[Dict[str, str]]:
        """Создает пары токен-сообщение для отправки батчем."""
        user_message_map = {
            notification.user_id: notification.message for notification in notifications
        }

        token_message_pairs = [
            {"token": token.fcm_token, "message": user_message_map[token.user_id]}
            for token in tokens
            if token.user_id in user_message_map
        ]

        return token_message_pairs

    async def listen_for_notifications(
        self, sio: CustomSocketServer, user_id: int, redis_pool: RedisPool
    ) -> None:
        await self.notification_service.listen_for_notifications(
            sio, user_id, redis_pool
        )

    async def notify_new_listing(self, listing: ListingDTO) -> None:
        user_ids = []

        category_id = listing.category_id
        subcategory_id = listing.subcategory_id

        category_views: List[UserView] = (
            await self.category_view_service.get_interested_users_by_category_id(
                category_id
            )
        )
        subcategory_views: List[UserView] = (
            await self.subcategory_view_service.get_interested_users_by_subcategory_id(
                subcategory_id
            )
        )

        notifications = []

        for user in subcategory_views:
            notifications.append(
                NotificationSchema(
                    user_id=user.user_id,
                    message="notifications.interesting_subcategory.new_listing",
                )
            )
            user_ids.append(user.user_id)

        subcategory_user_ids = {user.user_id for user in subcategory_views}
        for user in category_views:
            if user.user_id not in subcategory_user_ids:
                notifications.append(
                    NotificationSchema(
                        user_id=user.user_id,
                        message="notifications.interesting_category.new_listing",
                    )
                )
                user_ids.append(user.user_id)

        excluded_ids = await self.notification_settings_service.get_users_with_disabled_listing_notifications(
            user_ids
        )
        filtered_notifications = [
            notification
            for notification in notifications
            if notification.user_id not in excluded_ids
        ]
        await self.make_notifications(filtered_notifications)

    async def make_notifications(self, notifications: List[NotificationSchema]) -> None:
        user_ids = []
        await self.uow.begin()
        session = await self.uow.get_session()
        for notification in notifications:
            user_ids.append(notification.user_id)
            await self.notification_service.create_notification(notification, session)
        await self.uow.commit()

        fcm_tokens = await self.fcm_token_service.get_frm_tokens_by_user_ids(user_ids)
        token_message_pairs = self._create_token_message_pairs(
            fcm_tokens, notifications
        )
        failed_tokens = self.notification_service.send_fcm_notifications(
            token_message_pairs
        )
        if len(failed_tokens) > 0:
            await self.fcm_token_service.delete_tokens_by_tokens(failed_tokens)
        await self.notification_service.notify_users(
            notifications, redis_pool=self.redis_pool
        )
        # TODO Реализовать бэкграунд таской и раскомментить при деплое не на таймвеб
        # emails = await self.user_service.get_emails_by_user_ids(user_ids)
        # for email in emails:
        #     await self.email_sender.send_email(email=emails)

    async def add_fcm_token(
        self, token_data: FCMTokenSchema, user: UserDTO
    ) -> AddFCMTokenResponse:
        existing_token = await self.fcm_token_service.get_fcm_token_by_device_id(
            token_data.device_id
        )
        if existing_token:
            if existing_token.user_id == user.id:
                await self.fcm_token_service.update_fcm_token_by_id(
                    existing_token.id, token_data.fcm_token
                )
        else:
            await self.fcm_token_service.add_fcm_token(token_data, user.id)
        return AddFCMTokenResponse()

    async def delete_fcm_token(self, device_id: str, user: UserDTO) -> None:
        await self.fcm_token_service.delete_fcm_token_by_device_id(device_id, user.id)

    async def get_notifications(
        self, current_user: UserDTO, limit: int, offset: int, include_read: bool
    ) -> GetNotificationsResponse:
        notifications, count = (
            await self.notification_service.get_notifications_by_user_id(
                current_user.id, limit, offset, include_read
            )
        )
        return GetNotificationsResponse(data=notifications, count=count)

    async def read_notifications(
        self, payload: ReadNotificationsRequest, user: UserDTO
    ) -> ReadNotificationsResponse:
        await self.notification_service.read_notifications_by_ids(
            payload.notification_ids, user.id
        )
        return ReadNotificationsResponse()

    async def get_notification_settings(
        self, user: UserDTO
    ) -> GetNotificationSettingsResponse:
        settings = await self.notification_settings_service.get_notification_settings_by_user_id(
            user.id
        )
        return GetNotificationSettingsResponse(data=settings)

    async def update_notification_settings(
        self, payload: PutNotificationSettingsRequest, user: UserDTO
    ) -> PutNotificationSettingsResponse:
        await self.notification_settings_service.update_notification_settings(
            user.id, payload
        )
        return PutNotificationSettingsResponse()
