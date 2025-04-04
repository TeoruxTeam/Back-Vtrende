from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import BaseModel


class FCMToken(BaseModel):
    __tablename__ = "fcm_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    fcm_token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    device_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)


class NotificationSettings(BaseModel):
    __tablename__ = "notification_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    notify_new_messages: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_recommendations: Mapped[bool] = mapped_column(Boolean, default=True)


class Notification(BaseModel):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    message_key: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
