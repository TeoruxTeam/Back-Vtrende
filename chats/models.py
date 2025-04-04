import enum
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    case,
    func,
)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import BaseModel


class ListingChat(BaseModel):
    __tablename__ = "listing_chats"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id"), nullable=False, index=True
    )
    buyer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        index=True,
    )

    listing: Mapped["Listing"] = relationship(back_populates="chats")
    buyer: Mapped["User"] = relationship(back_populates="chats_as_buyer")
    messages: Mapped[List["ListingChatMessage"]] = relationship(
        back_populates="chat", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("listing_id", "buyer_id", name="uq_listing_buyer"),
    )


class ListingChatMessage(BaseModel):
    __tablename__ = "listing_chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("listing_chats.id"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    message: Mapped[str] = mapped_column(String(5000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    chat: Mapped["ListingChat"] = relationship(back_populates="messages")
    user: Mapped["User"] = relationship(back_populates="messages")


from items.models import Listing
from users.models import User
