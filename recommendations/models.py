from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from core.database import BaseModel


class UserCategoryView(BaseModel):
    __tablename__ = "category_views"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    view_count: Mapped[int] = mapped_column(BigInteger)


class UserSubcategoryView(BaseModel):
    __tablename__ = "subcategory_views"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    subcategory_id: Mapped[int] = mapped_column(ForeignKey("subcategories.id"))
    view_count: Mapped[int] = mapped_column(BigInteger)
