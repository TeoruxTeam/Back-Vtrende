from abc import ABC, abstractmethod
from typing import Dict, List

from sqlalchemy import insert, update
from sqlalchemy.future import select

from core.repositories import BaseRepository

from .mappers import UserCategoryViewMapper, UserSubcategoryViewMapper
from .models import UserCategoryView, UserSubcategoryView
from .schemas import UserCategoryViewFromORM, UserSubcategoryViewFromORM, UserView


class ICategoryViewRepository(ABC):

    @abstractmethod
    async def get_view_count(
        self, user_id: int, category_id: int
    ) -> UserCategoryViewFromORM | None:
        """Retrieve the current view count for a given category and user."""
        pass

    @abstractmethod
    async def increment_existing_view(self, user_id: int, category_id: int) -> None:
        """Increment the view count of an existing entry."""
        pass

    @abstractmethod
    async def create_view_count(self, user_id: int, category_id: int) -> None:
        """Create a new entry for view count with an initial value."""
        pass

    @abstractmethod
    async def get_interested_users_by_category_id(
        self, category_id: int
    ) -> List[UserView]:
        pass


class ISubcategoryViewRepository(ABC):

    @abstractmethod
    async def get_view_count(
        self, user_id: int, subcategory_id: int
    ) -> UserSubcategoryViewFromORM | None:
        """Retrieve the current view count for a given subcategory and user."""
        pass

    @abstractmethod
    async def increment_existing_view(self, user_id: int, subcategory_id: int) -> None:
        """Increment the view count of an existing entry."""
        pass

    @abstractmethod
    async def create_view_count(self, user_id: int, subcategory_id: int) -> None:
        """Create a new entry for view count with an initial value."""
        pass

    @abstractmethod
    async def get_interested_users_by_subcategory_id(
        self, subcategory_id: int
    ) -> List[UserView]:
        pass


class CategoryViewRepository(ICategoryViewRepository, BaseRepository):

    async def get_view_count(
        self, user_id: int, category_id: int
    ) -> UserCategoryViewFromORM | None:
        async with self.get_session() as session:
            stmt = select(UserCategoryView).where(
                UserCategoryView.user_id == user_id,
                UserCategoryView.category_id == category_id,
            )
            result = await session.execute(stmt)
            count = result.scalar()
            if count:
                return UserCategoryViewMapper.from_orm(count)
            return None

    async def increment_existing_view(self, user_id: int, category_id: int) -> None:
        async with self.get_session() as session:
            update_stmt = (
                update(UserCategoryView)
                .where(
                    UserCategoryView.user_id == user_id,
                    UserCategoryView.category_id == category_id,
                )
                .values(view_count=UserCategoryView.view_count + 1)
            )
            await session.execute(update_stmt)
            await session.commit()

    async def create_view_count(self, user_id: int, category_id: int) -> None:
        async with self.get_session() as session:
            category_view = UserCategoryView(
                user_id=user_id, category_id=category_id, view_count=1
            )
            session.add(category_view)
            await session.commit()

    async def get_interested_users_by_category_id(
        self, category_id: int
    ) -> List[UserView]:
        """
        Returns a dictionary of user_ids and their view counts for users who have viewed
        a given category at least 5 times.
        """
        async with self.get_session() as session:
            results = await session.execute(
                select(UserCategoryView.user_id, UserCategoryView.view_count).where(
                    UserCategoryView.category_id == category_id,
                    UserCategoryView.view_count >= 5,
                )
            )

            return [
                UserCategoryViewMapper.user_view_from_row(row)
                for row in results.fetchall()
            ]


class SubcategoryViewRepository(ISubcategoryViewRepository, BaseRepository):

    async def get_view_count(
        self, user_id: int, subcategory_id: int
    ) -> UserSubcategoryViewFromORM | None:
        async with self.get_session() as session:
            stmt = select(UserSubcategoryView).where(
                UserSubcategoryView.user_id == user_id,
                UserSubcategoryView.subcategory_id == subcategory_id,
            )
            result = await session.execute(stmt)
            count = result.scalar()
            if count:
                return UserSubcategoryViewMapper.from_orm(count)
            return None

    async def increment_existing_view(self, user_id: int, subcategory_id: int) -> None:
        async with self.get_session() as session:
            update_stmt = (
                update(UserSubcategoryView)
                .where(
                    UserSubcategoryView.user_id == user_id,
                    UserSubcategoryView.subcategory_id == subcategory_id,
                )
                .values(view_count=UserSubcategoryView.view_count + 1)
            )
            await session.execute(update_stmt)
            await session.commit()

    async def create_view_count(self, user_id: int, subcategory_id: int) -> None:
        async with self.get_session() as session:
            view_count = UserSubcategoryView(
                user_id=user_id, subcategory_id=subcategory_id, view_count=1
            )
            session.add(view_count)
            await session.commit()

    async def get_interested_users_by_subcategory_id(
        self, subcategory_id: int
    ) -> List[UserView]:
        """
        Returns a dictionary of user_ids and their view counts for users who have viewed
        a given subcategory at least 5 times.
        """
        async with self.get_session() as session:
            results = await session.execute(
                select(
                    UserSubcategoryView.user_id, UserSubcategoryView.view_count
                ).where(
                    UserSubcategoryView.subcategory_id == subcategory_id,
                    UserSubcategoryView.view_count >= 5,
                )
            )

            return [
                UserCategoryViewMapper.user_view_from_row(row)
                for row in results.fetchall()
            ]
