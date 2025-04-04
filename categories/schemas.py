from typing import List, Optional

from pydantic import BaseModel

from core.schemas import StatusOkSchema


class CategoryFromORM(BaseModel):
    id: int
    name_localization_key_id: int


class CategoryWithLocalizationKey(CategoryFromORM):
    name_localization_key: str


class SubcategoryFromORM(CategoryFromORM):
    category_id: int


class SubcategoryWithLocalizationKey(CategoryWithLocalizationKey):
    category_id: int


class CategoryWithLocalization(BaseModel):
    id: int
    localized_name: Optional[str]


class SubcategoryWithLocalization(BaseModel):
    id: int
    localized_name: Optional[str]
    category_id: int


class CategorySchema(BaseModel):
    id: int
    name: str


class SubcategorySchema(CategorySchema):
    category_id: int


class GetCategoriesResponseSchema(StatusOkSchema):
    data: List[CategoryWithLocalization]


class GetSubcategoriesResponseSchema(StatusOkSchema):
    data: List[SubcategoryWithLocalization]


class AdminCreateCategoryResponse(StatusOkSchema):
    message: str = "success.admin.category.created"
    data: CategoryWithLocalizationKey


class AdminPutCategoryResponse(StatusOkSchema):
    message: str = "success.admin.category.updated"
    data: CategoryWithLocalizationKey


class AdminCreateSubcategoryResponse(StatusOkSchema):
    message: str = "success.admin.subcategory.created"
    data: SubcategoryWithLocalizationKey


class AdminPutSubcategoryResponse(StatusOkSchema):
    message: str = "success.admin.subcategory.updated"
    data: SubcategoryWithLocalizationKey
