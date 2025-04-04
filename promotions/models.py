from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from core.database import BaseModel


class PromotionTariff(BaseModel):
    __tablename__ = "promotion_tariffs"

    __table_args__ = (
        CheckConstraint("priority > 0", name="check_priority_positive"),
        Index(
            "unique_active_tariff_name",
            "name_localization_key_id",
            unique=True,
            postgresql_where=expression.text("is_deleted = FALSE"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name_localization_key_id: Mapped[int] = mapped_column(
        ForeignKey("localization_keys.id"), nullable=False
    )
    price: Mapped[Decimal] = mapped_column(nullable=False)
    duration_days: Mapped[int] = mapped_column(nullable=False)
    description_localization_key_id: Mapped[int] = mapped_column(
        ForeignKey("localization_keys.id"), nullable=False
    )
    priority: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    promotion_orders: Mapped["PromotionOrder"] = relationship(
        back_populates="tariff",
        passive_deletes="all",
    )

    name_localization_key: Mapped["LocalizationKey"] = relationship(
        "LocalizationKey",
        foreign_keys=[name_localization_key_id],
    )

    # Отношение к локализационному ключу для описания
    description_localization_key: Mapped["LocalizationKey"] = relationship(
        "LocalizationKey",
        foreign_keys=[description_localization_key_id],
    )


class PromotionOrder(BaseModel):
    __tablename__ = "promotion_orders"

    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'PAID', 'CANCELLED')", name="check_status_valid"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id"), nullable=False, index=True
    )
    tariff_id: Mapped[int] = mapped_column(
        ForeignKey("promotion_tariffs.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="PENDING")
    start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
    )

    listing: Mapped["Listing"] = relationship(
        "Listing", back_populates="promotion_orders"
    )
    tariff: Mapped["PromotionTariff"] = relationship(back_populates="promotion_orders")


from listings.models import Listing
from localization.models import LocalizationKey
