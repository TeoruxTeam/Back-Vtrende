from abc import ABC, abstractmethod
from typing import List, Optional

from .exceptions import CategoryNotFound
from .schemas import (
    CategorySchema,
    CategoryWithLocalization,
    GetCategoriesResponseSchema,
    GetSubcategoriesResponseSchema,
    SubcategorySchema,
    SubcategoryWithLocalization,
)
from .services import ICategoryService, ISubcategoryService


class ICategoryFacade(ABC):

    @abstractmethod
    async def get_categories_with_localization(
        self, language: str
    ) -> GetCategoriesResponseSchema:
        pass

    @abstractmethod
    async def get_subcategories_with_localization(
        self, category_id: int, language: str
    ) -> GetSubcategoriesResponseSchema:
        pass


class CategoryFacade(ICategoryFacade):

    def __init__(
        self,
        category_service: ICategoryService,
        subcategory_service: ISubcategoryService,
    ):
        self.category_service = category_service
        self.subcategory_service = subcategory_service

    async def get_categories_with_localization(
        self, language: str
    ) -> GetCategoriesResponseSchema:
        categories: List[CategoryWithLocalization] = (
            await self.category_service.get_categories_with_localization(language)
        )
        return GetCategoriesResponseSchema(data=categories)

    async def get_subcategories_with_localization(
        self, category_id: int, language: str
    ) -> GetSubcategoriesResponseSchema:
        category = await self.category_service.get_category_by_id(category_id)
        if category is None:
            raise CategoryNotFound
        subcategories: List[SubcategoryWithLocalization] = (
            await self.subcategory_service.get_subcategories(category_id, language)
        )
        return GetSubcategoriesResponseSchema(data=subcategories)
