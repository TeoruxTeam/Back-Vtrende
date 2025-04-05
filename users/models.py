from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=True)
    password: Mapped[str] = mapped_column(String(128), nullable=True)
    is_shop: Mapped[bool] = mapped_column(Boolean)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    iin_bin: Mapped[str] = mapped_column(String(12), nullable=True)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user"
    )
    recovery_token: Mapped["RecoveryToken"] = relationship(
        back_populates="user"
    )
    verification_token: Mapped["VerificationToken"] = relationship(
        back_populates="user"
    )
    items: Mapped[list["Item"]] = relationship(back_populates="shop")
    favorite_items: Mapped[list["FavoriteItem"]] = relationship(
        back_populates="user"
    )
    favorite_shops: Mapped[list["FavoriteShop"]] = relationship(
        back_populates="user", foreign_keys="FavoriteShop.user_id"
    )
    favorited_by: Mapped[list["FavoriteShop"]] = relationship(
        back_populates="shop", foreign_keys="FavoriteShop.shop_id"
    )


from accounts.models import RecoveryToken, VerificationToken
from auth.models import RefreshToken
from items.models import Item
from favorites.models import FavoriteShop, FavoriteItem