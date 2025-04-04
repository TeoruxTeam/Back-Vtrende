from typing import List

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import BaseModel


class Localization(BaseModel):
    __tablename__ = "localizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    localization_key_id: Mapped[int] = mapped_column(
        ForeignKey("localization_keys.id"), nullable=False, index=True
    )
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)

    localization_key: Mapped["LocalizationKey"] = relationship(
        "LocalizationKey", back_populates="localizations"
    )


class LocalizationKey(BaseModel):
    __tablename__ = "localization_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )

    localizations: Mapped[List["Localization"]] = relationship(
        back_populates="localization_key"
    )
