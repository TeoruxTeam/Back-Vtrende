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
    Integer
)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import BaseModel


class Item(BaseModel):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    photo: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String(255), nullable=False)

    shop_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    shop: Mapped["User"] = relationship(back_populates="items")
    favorite_items: Mapped[list["FavoriteItem"]] = relationship(back_populates="item")


from users.models import User
from favorites.models import FavoriteItem