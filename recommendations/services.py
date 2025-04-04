from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from sqlalchemy.exc import IntegrityError

from .repositories import ICategoryViewRepository, ISubcategoryViewRepository
from .schemas import UserView


class ICategoryViewService(ABC):

    @abstractmethod
    async def create_or_increment_views(self, user_id: int, category_id: int):
        pass

    @abstractmethod
    async def get_interested_users_by_category_id(
        self, category_id: int
    ) -> List[UserView]:
        pass


class ISubcategoryViewService(ABC):

    @abstractmethod
    async def create_or_increment_views(self, user_id: int, subcategory_id: int):
        pass

    @abstractmethod
    async def get_interested_users_by_subcategory_id(
        self, subcategory_id: int
    ) -> List[UserView]:
        pass


class CategoryViewService(ICategoryViewService):

    def __init__(self, repo: ICategoryViewRepository):
        self.repo = repo

    async def create_or_increment_views(self, user_id: int, category_id: int):
        try:
            existing_count = await self.repo.get_view_count(user_id, category_id)
            if existing_count:
                await self.repo.increment_existing_view(user_id, category_id)
                return None
            await self.repo.create_view_count(user_id, category_id)
        except IntegrityError:
            pass

    async def get_interested_users_by_category_id(
        self, category_id: int
    ) -> List[UserView]:
        return await self.repo.get_interested_users_by_category_id(category_id)


class SubcategoryViewService(ISubcategoryViewService):

    def __init__(self, repo: ISubcategoryViewRepository):
        self.repo = repo

    async def create_or_increment_views(self, user_id: int, subcategory_id: int):
        try:
            existing_count = await self.repo.get_view_count(user_id, subcategory_id)
            if existing_count:
                await self.repo.increment_existing_view(user_id, subcategory_id)
                return None
            await self.repo.create_view_count(user_id, subcategory_id)
        except IntegrityError:
            pass

    async def get_interested_users_by_subcategory_id(
        self, subcategory_id: int
    ) -> List[UserView]:
        return await self.repo.get_interested_users_by_subcategory_id(subcategory_id)
