from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from core.container import Container
from core.utils import get_language_from_cookies

from .facade import ICategoryFacade
from .schemas import GetCategoriesResponseSchema, GetSubcategoriesResponseSchema

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
)


@router.get("/", response_model=GetCategoriesResponseSchema)
@inject
async def get_categories(
    language: str = Depends(get_language_from_cookies),
    category_facade: ICategoryFacade = Depends(Provide[Container.category_facade]),
):
    return await category_facade.get_categories_with_localization(language)


@router.get(
    "/{category_id}/subcategories/", response_model=GetSubcategoriesResponseSchema
)
@inject
async def get_subcategories(
    category_id: int,
    language: str = Depends(get_language_from_cookies),
    category_facade: ICategoryFacade = Depends(Provide[Container.category_facade]),
):
    return await category_facade.get_subcategories_with_localization(
        category_id, language
    )
