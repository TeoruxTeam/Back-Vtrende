from typing import List

from .models import Category, Subcategory
from .schemas import (
    CategoryFromORM,
    CategoryWithLocalization,
    CategoryWithLocalizationKey,
    SubcategoryFromORM,
    SubcategoryWithLocalization,
    SubcategoryWithLocalizationKey,
)


class CategoryMapper:

    @staticmethod
    def to_category_with_localization_key(
        category: CategoryFromORM, name_localization_key: str
    ) -> CategoryWithLocalizationKey:
        return CategoryWithLocalizationKey(
            id=category.id,
            name_localization_key_id=category.name_localization_key_id,
            name_localization_key=name_localization_key,
        )

    @staticmethod
    def to_category_from_orm(category: Category) -> CategoryFromORM:
        return CategoryFromORM(
            id=category.id,
            name_localization_key_id=category.name_localization_key_id,
        )

    @staticmethod
    def to_category_with_localization(
        category: Category, localization_value: str
    ) -> CategoryWithLocalization:
        return CategoryWithLocalization(
            id=category.id,
            localized_name=localization_value,
        )


class SubcategoryMapper:

    @staticmethod
    def to_subcategory_with_localization(
        subcategory: Subcategory, localization_value: str
    ) -> SubcategoryWithLocalization:
        return SubcategoryWithLocalization(
            id=subcategory.id,
            category_id=subcategory.category_id,
            localized_name=localization_value,
        )

    @staticmethod
    def to_subcategory_from_orm_list(
        subcategories: List[Subcategory],
    ) -> List[SubcategoryFromORM]:
        return [
            SubcategoryMapper.to_subcategory_from_orm(subcategory)
            for subcategory in subcategories
        ]

    @staticmethod
    def to_subcategory_from_orm(subcategory: Subcategory) -> SubcategoryFromORM:
        return SubcategoryFromORM(
            id=subcategory.id,
            name_localization_key_id=subcategory.name_localization_key_id,
            category_id=subcategory.category_id,
        )

    @staticmethod
    def to_subcategory_with_localization_key(
        subcategory: SubcategoryFromORM, name_localization_key: str
    ) -> SubcategoryWithLocalizationKey:
        return SubcategoryWithLocalizationKey(
            id=subcategory.id,
            name_localization_key_id=subcategory.name_localization_key_id,
            name_localization_key=name_localization_key,
            category_id=subcategory.category_id,
        )
