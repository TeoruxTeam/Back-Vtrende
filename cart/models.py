from sqlalchemy import Column, Integer, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import relationship
from core.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime


class Cart(Base):
    __tablename__ = "cart"
    __table_args__ = (
        UniqueConstraint("user_id", "item_id", name="unique_user_item_cart"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    
    user: Mapped["User"] = relationship(back_populates="cart")
    item: Mapped["Item"] = relationship(back_populates="cart")


from users.models import User
from items.models import Item
