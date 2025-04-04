from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from admin.schemas import (
    AdminCreateCategoryRequest,
    AdminCreateSubcategoryRequest,
    AdminPutCategoryRequest,
    AdminPutSubcategoryRequest,
)

from .exceptions import CategoryNotFound
from .repositories import ICategoryRepository, ISubcategoryRepository
from .schemas import (
    CategoryFromORM,
    CategorySchema,
    CategoryWithLocalization,
    GetCategoriesResponseSchema,
    GetSubcategoriesResponseSchema,
    SubcategoryFromORM,
    SubcategorySchema,
    SubcategoryWithLocalization,
)


class ICategoryService(ABC):

    @abstractmethod
    async def get_categories_with_localization(
        self, language: str
    ) -> List[CategoryWithLocalization]:
        pass

    @abstractmethod
    async def get_category_with_localization_by_id(
        self, category_id: int, language: str
    ) -> CategoryWithLocalization:
        pass

    @abstractmethod
    async def get_category_by_id(self, category_id: int) -> Optional[CategoryFromORM]:
        pass

    @abstractmethod
    async def create_category(
        self, name_localization_key_id: int, session: AsyncSession
    ) -> CategoryFromORM:
        pass

    @abstractmethod
    async def update_category(
        self, category_id: int, schema: AdminPutCategoryRequest
    ) -> None:
        pass

    @abstractmethod
    async def delete_category(
        self, category_id: int, session: Optional[AsyncSession]
    ) -> None:
        pass


class CategoryService(ICategoryService):

    def __init__(self, repo: ICategoryRepository):
        self.repo = repo

    async def get_categories_with_localization(
        self, language: str
    ) -> List[CategoryWithLocalization]:
        return await self.repo.get_categories_with_localization(language)

    async def get_category_with_localization_by_id(
        self, category_id: int, language: str
    ) -> CategoryWithLocalization:
        return await self.repo.get_category_with_localization_by_id(
            category_id, language
        )

    async def get_category_by_id(self, category_id: int) -> Optional[CategoryFromORM]:
        return await self.repo.get_category_by_id(category_id)

    async def create_category(
        self, name_localization_key_id: int, session: AsyncSession
    ) -> CategoryFromORM:
        return await self.repo.create_category(name_localization_key_id, session)

    async def update_category(
        self, category_id: int, schema: AdminPutCategoryRequest
    ) -> None:
        await self.repo.update_category(category_id, schema)

    async def delete_category(
        self, category_id: int, session: Optional[AsyncSession]
    ) -> None:
        await self.repo.delete_category(category_id, session)


class ISubcategoryService(ABC):

    @abstractmethod
    async def get_subcategories(
        self, category_id: int, language: str
    ) -> List[SubcategoryWithLocalization]:
        pass

    @abstractmethod
    async def get_subcategory_with_localization_by_id(
        self, subcategory_id: int, language: str
    ) -> SubcategoryWithLocalization:
        pass

    @abstractmethod
    async def get_subcategory_by_id(self, subcategory_id: int) -> SubcategorySchema:
        pass

    @abstractmethod
    async def create_subcategory(
        self,
        name_localization_key_id: int,
        category_id: int,
        session: Optional[AsyncSession],
    ) -> SubcategoryFromORM:
        pass

    @abstractmethod
    async def update_subcategory(
        self, subcategory_id: int, schema: AdminPutSubcategoryRequest
    ) -> None:
        pass

    @abstractmethod
    async def delete_subcategory(
        self, subcategory_id: int, session: Optional[AsyncSession]
    ) -> None:
        pass


class SubcategoryService(ISubcategoryService):

    def __init__(self, repo: ISubcategoryRepository):
        self.repo = repo

    async def get_subcategories(
        self, category_id: int, language: str
    ) -> List[CategoryWithLocalization]:
        return await self.repo.get_subcategories_with_localization(
            category_id, language
        )

    async def get_subcategory_with_localization_by_id(
        self, subcategory_id: int, language: str
    ) -> SubcategoryWithLocalization:
        return await self.repo.get_subcategory_with_localization_by_id(
            subcategory_id, language
        )

    async def get_subcategory_by_id(
        self, subcategory_id: int
    ) -> Optional[SubcategorySchema]:
        return await self.repo.get_subcategory_by_id(subcategory_id)

    async def create_subcategory(
        self,
        name_localization_key_id: int,
        category_id: int,
        session: Optional[AsyncSession],
    ) -> SubcategoryFromORM:
        return await self.repo.create_subcategory(
            name_localization_key_id, category_id, session
        )

    async def update_subcategory(
        self, subcategory_id: int, schema: AdminPutSubcategoryRequest
    ) -> SubcategorySchema:
        await self.repo.update_subcategory(subcategory_id, schema)

    async def delete_subcategory(
        self, subcategory_id: int, session: Optional[AsyncSession]
    ) -> None:
        await self.repo.delete_subcategory(subcategory_id, session)
