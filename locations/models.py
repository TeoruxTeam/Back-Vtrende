from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import BaseModel


class Location(BaseModel):
    """
    Represents a physical location. Contains latitude and longitude coordinates.
    The coordinates are of type Decimal to avoid floating point errors during external API calls.
    """

    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)

    latitude: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=True, index=True)
    longitude: Mapped[Decimal] = mapped_column(
        Numeric(11, 8), nullable=True, index=True
    )
    address: Mapped[String] = mapped_column(String(1000), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )

    listings: Mapped["Listing"] = relationship(back_populates="location")


from listings.models import Listing
