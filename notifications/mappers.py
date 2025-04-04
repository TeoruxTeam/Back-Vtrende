from .models import FCMToken, Notification, NotificationSettings
from .schemas import (
    FCMTokenFromORM,
    FCMTokenSchema,
    NotificationFromORM,
    NotificationSchema,
    NotificationSettingsFromORM,
)


class NotificationMapper:

    @staticmethod
    def from_schema_to_entity(schema: NotificationSchema) -> Notification:
        return Notification(
            user_id=schema.user_id,
            message_key=schema.message,
        )

    @staticmethod
    def from_orm(schema: Notification) -> NotificationFromORM:
        return NotificationFromORM(
            id=schema.id,
            user_id=schema.user_id,
            message_key=schema.message_key,
            created_at=schema.created_at,
            is_read=schema.is_read,
        )


class FCMTokenMapper:

    @staticmethod
    def to_schema_from_orm(entity: FCMToken) -> FCMTokenFromORM:
        return FCMTokenFromORM(
            id=entity.id,
            user_id=entity.user_id,
            fcm_token=entity.fcm_token,
            device_id=entity.device_id,
        )


class NotificationSettingsMapper:

    @staticmethod
    def to_schema_from_orm(entity: NotificationSettings) -> NotificationSettingsFromORM:
        return NotificationSettingsFromORM(
            id=entity.id,
            user_id=entity.user_id,
            notify_new_messages=entity.notify_new_messages,
            notify_recommendations=entity.notify_recommendations,
        )
