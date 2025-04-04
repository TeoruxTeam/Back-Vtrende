from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy import and_, delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from admin.schemas import (
    AdminCreateCategoryRequest,
    AdminCreateSubcategoryRequest,
    AdminPutCategoryRequest,
    AdminPutSubcategoryRequest,
)
from core.repositories import BaseRepository
from localization.models import Localization, LocalizationKey

from .exceptions import CategoryChildExists, SubcategoryChildExists
from .mappers import CategoryMapper, SubcategoryMapper
from .models import Category, Subcategory
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


class ICategoryRepository(ABC):

    @abstractmethod
    async def get_categories_with_localization(
        self, language: str
    ) -> List[CategoryWithLocalization]:
        pass

    @abstractmethod
    async def get_category_by_id(self, category_id: int) -> CategoryFromORM:
        pass

    @abstractmethod
    async def create_category(
        self, name_localization_key_id: int, external_session: Optional[AsyncSession]
    ) -> CategoryFromORM:
        pass

    @abstractmethod
    async def update_category(
        self, category_id: int, schema: AdminPutCategoryRequest
    ) -> None:
        pass

    @abstractmethod
    async def delete_category(
        self, category_id: int, external_session: Optional[AsyncSession]
    ) -> None:
        pass

    @abstractmethod
    async def get_category_with_localization_by_id(
        self, category_id: int, language: str
    ) -> CategoryWithLocalization:
        pass


class ISubcategoryRepository(ABC):

    @abstractmethod
    async def get_subcategories_with_localization(
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
        external_session: Optional[AsyncSession],
    ) -> SubcategoryFromORM:
        pass

    @abstractmethod
    async def update_subcategory(
        self, subcategory_id: int, schema: AdminPutSubcategoryRequest
    ) -> None:
        pass

    @abstractmethod
    async def delete_subcategory(
        self, subcategory_id: int, external_session: Optional[AsyncSession]
    ) -> None:
        pass


class CategoryRepository(ICategoryRepository, BaseRepository):

    async def get_categories_with_localization(
        self, language: str
    ) -> List[CategoryWithLocalization]:
        async with self.get_session() as session:
            query = (
                select(Category, Localization.value)
                .join(
                    LocalizationKey,
                    Category.name_localization_key_id == LocalizationKey.id,
                )
                .join(
                    Localization,
                    and_(
                        Localization.localization_key_id == LocalizationKey.id,
                        Localization.language == language,
                    ),
                    isouter=True,
                )
                .order_by(Category.id)
            )
            result = await session.execute(query)
            categories = [
                CategoryMapper.to_category_with_localization(
                    category, localization_value
                )
                for category, localization_value in result.fetchall()
            ]
            return categories

    async def get_category_with_localization_by_id(
        self, category_id: int, language: str
    ) -> CategoryWithLocalization:
        async with self.get_session() as session:
            query = (
                select(Category, Localization.value)
                .join(
                    LocalizationKey,
                    Category.name_localization_key_id == LocalizationKey.id,
                )
                .join(
                    Localization,
                    and_(
                        Localization.localization_key_id == LocalizationKey.id,
                        Localization.language == language,
                    ),
                    isouter=True,  # Используем LEFT JOIN для включения категорий без локализации
                )
                .filter(Category.id == category_id)
            )
            result = await session.execute(query)

            # Получаем результат запроса
            row = result.one_or_none()
            if row is None:
                # Если категория не найдена, можно вернуть None или выбросить ошибку
                return None

            # Распаковка данных (localization_value будет None, если локализация отсутствует)
            category, localization_value = row

            return CategoryMapper.to_category_with_localization(
                category, localization_value
            )

    async def get_category_by_id(self, category_id: int) -> Optional[CategoryFromORM]:
        async with self.get_session() as session:
            query = select(Category).filter(Category.id == category_id)
            result = await session.execute(query)
            category = result.scalar()
            if not category:
                return None
            return CategoryMapper.to_category_from_orm(category)

    async def create_category(
        self, name_localization_key_id: int, external_session: Optional[AsyncSession]
    ) -> CategoryFromORM:
        async with self.get_session(external_session) as session:
            category = Category(name_localization_key_id=name_localization_key_id)
            session.add(category)
            if not external_session:
                await session.commit()
                await session.refresh(category)
            else:
                await session.flush()
            return CategoryMapper.to_category_from_orm(category)

    async def update_category(
        self, category_id: int, schema: AdminPutCategoryRequest
    ) -> None:
        async with self.get_session() as session:
            query = (
                update(Category)
                .where(Category.id == category_id)
                .values(name=schema.name)
            )
            await session.execute(query)
            await session.commit()

    async def delete_category(
        self, category_id: int, external_session: Optional[AsyncSession]
    ) -> None:
        async with self.get_session(external_session) as session:
            try:
                query = delete(Category).where(Category.id == category_id)
                await session.execute(query)
                if external_session:
                    await session.flush()
                else:
                    await session.commit()
            except IntegrityError:
                await session.rollback()
                raise CategoryChildExists()


class SubcategoryRepository(ISubcategoryRepository, BaseRepository):

    async def get_subcategories_with_localization(
        self, category_id: int, language: str
    ) -> List[SubcategoryWithLocalization]:
        async with self.get_session() as session:
            query = (
                select(Subcategory, Localization.value)
                .join(
                    LocalizationKey,
                    Subcategory.name_localization_key_id == LocalizationKey.id,
                )
                .join(
                    Localization,
                    and_(
                        Localization.localization_key_id == LocalizationKey.id,
                        Localization.language == language,
                    ),
                    isouter=True,
                )
                .filter(Subcategory.category_id == category_id)
                .order_by(Subcategory.id)
            )
            result = await session.execute(query)
            subcategories = [
                SubcategoryMapper.to_subcategory_with_localization(
                    subcategory, localization_value
                )
                for subcategory, localization_value in result.fetchall()
            ]
            return subcategories

    async def get_subcategory_with_localization_by_id(
        self, subcategory_id: int, language: str
    ) -> SubcategoryWithLocalization:
        async with self.get_session() as session:
            query = (
                select(Subcategory, Localization.value)
                .join(
                    LocalizationKey,
                    Subcategory.name_localization_key_id == LocalizationKey.id,
                )
                .join(
                    Localization,
                    and_(
                        Localization.localization_key_id == LocalizationKey.id,
                        Localization.language == language,
                    ),
                    isouter=True,
                )
                .filter(Subcategory.id == subcategory_id)
            )
            result = await session.execute(query)
            row = result.one_or_none()

            if row is None:
                return None

            subcategory, localization_value = row
            return SubcategoryMapper.to_subcategory_with_localization(
                subcategory, localization_value
            )

    async def get_subcategory_by_id(
        self, subcategory_id: int
    ) -> Optional[SubcategorySchema]:
        async with self.get_session() as session:
            query = select(Subcategory).filter(Subcategory.id == subcategory_id)
            result = await session.execute(query)
            subcategory = result.scalar()
            if not subcategory:
                return None
            return SubcategoryMapper.to_subcategory_from_orm(subcategory)

    async def create_subcategory(
        self,
        name_localization_key_id: int,
        category_id: int,
        external_session: Optional[AsyncSession],
    ) -> SubcategoryFromORM:
        async with self.get_session(external_session) as session:
            subcategory = Subcategory(
                category_id=category_id,
                name_localization_key_id=name_localization_key_id,
            )
            session.add(subcategory)
            if not external_session:
                await session.commit()
                await session.refresh(subcategory)
            else:
                await session.flush()
            return SubcategoryMapper.to_subcategory_from_orm(subcategory)

    async def update_subcategory(
        self, subcategory_id: int, schema: AdminPutSubcategoryRequest
    ) -> None:
        async with self.get_session() as session:
            query = (
                update(Subcategory)
                .where(Subcategory.id == subcategory_id)
                .values(name=schema.name, category_id=schema.category_id)
            )
            await session.execute(query)
            await session.commit()

    async def delete_subcategory(
        self, subcategory_id: int, external_session: Optional[AsyncSession]
    ) -> None:
        async with self.get_session(external_session) as session:
            try:
                query = delete(Subcategory).where(Subcategory.id == subcategory_id)
                await session.execute(query)
                if external_session:
                    await session.flush()
                else:
                    await session.commit()
            except IntegrityError:
                await session.rollback()
                raise SubcategoryChildExists()
