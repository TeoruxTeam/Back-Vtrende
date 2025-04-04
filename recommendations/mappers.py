from typing import List

from .models import UserCategoryView, UserSubcategoryView
from .schemas import UserCategoryViewFromORM, UserSubcategoryViewFromORM, UserView


class UserCategoryViewMapper:

    @staticmethod
    def from_orm(count: UserCategoryView) -> UserCategoryViewFromORM:
        return UserCategoryViewFromORM(
            id=count.id,
            user_id=count.user_id,
            view_count=count.view_count,
            category_id=count.category_id,
        )

    @staticmethod
    def user_view_from_row(row) -> UserView:
        return UserView(user_id=row[0], view_count=row[1])


class UserSubcategoryViewMapper:

    @staticmethod
    def from_orm(count: UserSubcategoryView) -> UserSubcategoryViewFromORM:
        return UserSubcategoryViewFromORM(
            id=count.id,
            user_id=count.user_id,
            view_count=count.view_count,
            subcategory_id=count.subcategory_id,
        )

    @staticmethod
    def user_view_from_row(row) -> UserView:
        return UserView(user_id=row[0], view_count=row[1])
