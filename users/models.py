from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import BaseModel
from core.environment import env

from .schemas import UserDTO


class User(BaseModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    surname: Mapped[str] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    password: Mapped[str] = mapped_column(String(128), nullable=True)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)

    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_activated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    banned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    refresh_tokens: Mapped["RefreshToken"] = relationship(back_populates="user")
    verification_token: Mapped["VerificationToken"] = relationship(
        back_populates="user", uselist=False
    )
    recovery_token: Mapped["RecoveryToken"] = relationship(
        back_populates="user", uselist=False
    )
    listings: Mapped["Listing"] = relationship(back_populates="user")
    favorites_association: Mapped[List["FavoriteListing"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    favorites: Mapped[List["Listing"]] = association_proxy(
        "favorites_association", "listing"
    )
    chats_as_buyer: Mapped[List["ListingChat"]] = relationship(back_populates="buyer")
    messages: Mapped[List["ListingChatMessage"]] = relationship(back_populates="user")


from accounts.models import RecoveryToken, VerificationToken
from auth.models import RefreshToken
from chats.models import ListingChat, ListingChatMessage
from listings.models import FavoriteListing, Listing
