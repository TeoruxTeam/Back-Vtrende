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
    func,
)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import BaseModel


class ModerationStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Listing(BaseModel):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(5000), nullable=False)
    price: Mapped[int] = mapped_column(nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        index=True,
    )
    moderation_status: Mapped[ModerationStatus] = mapped_column(
        Enum(ModerationStatus, values_callable=lambda x: [e.value for e in x]),
        default=ModerationStatus.PENDING.value,
        index=True,
    )
    reject_reason: Mapped[str] = mapped_column(String(100), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    is_sold: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    sold_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), nullable=False, index=True
    )
    subcategory_id: Mapped[int] = mapped_column(
        ForeignKey("subcategories.id"), nullable=True, index=True
    )
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id"), nullable=True, index=True
    )

    user: Mapped["User"] = relationship(back_populates="listings")
    category: Mapped["Category"] = relationship(back_populates="listings")
    subcategory: Mapped["Subcategory"] = relationship(back_populates="listings")
    location: Mapped["Location"] = relationship(back_populates="listings")

    images: Mapped[List["ListingImage"]] = relationship(
        back_populates="listing", cascade="all, delete-orphan"
    )
    video: Mapped[Optional["ListingVideo"]] = relationship(
        back_populates="listing", uselist=False, cascade="all, delete-orphan"
    )
    favorited_by_association: Mapped[List["FavoriteListing"]] = relationship(
        back_populates="listing", cascade="all, delete-orphan"
    )

    favorited_by: Mapped[List["User"]] = association_proxy(
        "favorited_by_association", "user"
    )
    chats: Mapped[List["ListingChat"]] = relationship(back_populates="listing")
    promotion_orders: Mapped[List["PromotionOrder"]] = relationship(
        back_populates="listing",
        passive_deletes="all",  # Защищаем от каскадного удаления данных
    )


class ListingImage(BaseModel):
    __tablename__ = "listing_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    listing: Mapped["Listing"] = relationship(back_populates="images")


class ListingVideo(BaseModel):
    __tablename__ = "listing_videos"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    listing: Mapped["Listing"] = relationship(back_populates="video")


class FavoriteListing(BaseModel):
    __tablename__ = "user_favorite_listings"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), primary_key=True)

    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="favorites_association")
    listing: Mapped["Listing"] = relationship(
        "Listing", back_populates="favorited_by_association"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "listing_id", name="user_favorite_listing_uc"),
        Index("idx_user_id", "user_id"),
    )


from categories.models import Category, Subcategory
from chats.models import ListingChat
from locations.models import Location
from promotions.models import PromotionOrder
from users.models import User
