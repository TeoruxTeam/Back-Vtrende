from datetime import datetime
from typing import List

from pydantic import BaseModel

from core.schemas import CountSchema, StatusOkSchema


class NotificationSchema(BaseModel):
    user_id: int
    message: str


class NotificationFromORM(BaseModel):
    id: int
    user_id: int
    message_key: str
    created_at: datetime
    is_read: bool


class FCMTokenSchema(BaseModel):
    fcm_token: str
    device_id: str


class AddFCMTokenResponse(StatusOkSchema):
    message: str = "success.notifications.fcm_token.added"


class FCMTokenFromORM(FCMTokenSchema):
    id: int
    user_id: int


class GetNotificationsResponse(StatusOkSchema, CountSchema):
    data: List[NotificationFromORM]


class ReadNotificationsRequest(BaseModel):
    notification_ids: List[int]


class ReadNotificationsResponse(StatusOkSchema):
    message: str = "success.notifications.read"


class NotificationSettingsFromORM(BaseModel):
    id: int
    user_id: int
    notify_new_messages: bool
    notify_recommendations: bool


class PutNotificationSettingsResponse(StatusOkSchema):
    message: str = "success.notifications.settings.updated"


class GetNotificationSettingsResponse(StatusOkSchema):
    data: NotificationSettingsFromORM


class PutNotificationSettingsRequest(BaseModel):
    notify_new_messages: bool
    notify_recommendations: bool
