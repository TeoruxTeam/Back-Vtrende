from sqlalchemy import Column, Integer, ForeignKey, func, DateTime
from sqlalchemy.orm import relationship
from core.database import BaseModel
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column


class FavoriteItem(BaseModel):
    __tablename__ = "favorite_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )

    item: Mapped["Item"] = relationship(back_populates="favorite_items")
    user: Mapped["User"] = relationship(back_populates="favorite_items")


class FavoriteShop(BaseModel):
    __tablename__ = "favorite_shops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shop_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    shop: Mapped["User"] = relationship(
        back_populates="favorited_by", 
        foreign_keys=[shop_id]
    )
    user: Mapped["User"] = relationship(
        back_populates="favorite_shops", 
        foreign_keys=[user_id]
    )
from users.models import User
from items.models import Item


