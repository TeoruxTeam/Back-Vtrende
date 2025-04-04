from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, BigInteger, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import BaseModel


class ActivityStats(BaseModel):

    __tablename__ = "activity_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))



