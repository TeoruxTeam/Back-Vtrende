from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from core.database import BaseModel


class Rating(BaseModel):
    __tablename__ = "ratings"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="check_rating_range"),
        Index(
            "unique_user_listing_active",
            "user_id",
            "listing_id",
            unique=True,
            postgresql_where=(expression.text("is_deleted = FALSE")),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(String(255), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    user: Mapped["User"] = relationship("User")
    listing: Mapped["Listing"] = relationship("Listing")


from listings.models import Listing
from users.models import User
