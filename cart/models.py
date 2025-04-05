from sqlalchemy import Column, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from core.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime


class Cart(Base):
    __tablename__ = "cart"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    user: Mapped["User"] = relationship(back_populates="cart")
    item: Mapped["Item"] = relationship(back_populates="cart")
