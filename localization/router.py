import os

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from core.container import Container
from core.utils import get_language_from_cookies

from .facade import ILocalizationFacade

router = APIRouter(prefix="/localization")


@router.get("/translate/{key}/")
@inject
async def get_translation_key(
    key: str,
    language: str = Depends(get_language_from_cookies),
    localization_facade: ILocalizationFacade = Depends(
        Provide[Container.localization_facade]
    ),
):
    return await localization_facade.translate(language, key)


@router.get("/locales/{locale:str}/")
@inject
async def get_locale(
    locale: str,
    localization_facade: ILocalizationFacade = Depends(
        Provide[Container.localization_facade]
    ),
):
    """
    Позволяет фронту получить все переводы для указанного языка.
    """
    return await localization_facade.get_translation(locale)
