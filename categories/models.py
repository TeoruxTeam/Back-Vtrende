from decimal import Decimal
from typing import List

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import BaseModel


class Category(BaseModel):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name_localization_key_id: Mapped[int] = mapped_column(
        ForeignKey("localization_keys.id"), nullable=False
    )

    localization_key: Mapped["LocalizationKey"] = relationship("LocalizationKey")
    subcategories: Mapped[List["Subcategory"]] = relationship(back_populates="category")
    listings: Mapped[List["Listing"]] = relationship(back_populates="category")


class Subcategory(BaseModel):
    __tablename__ = "subcategories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name_localization_key_id: Mapped[int] = mapped_column(
        ForeignKey("localization_keys.id"), nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), nullable=False
    )

    localization_key: Mapped["LocalizationKey"] = relationship("LocalizationKey")
    category: Mapped["Category"] = relationship(back_populates="subcategories")
    listings: Mapped[List["Listing"]] = relationship(back_populates="subcategory")


from listings.models import Listing
