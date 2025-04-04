from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query

from auth.depends import get_current_confirmed_user
from core.container import Container
from core.utils import get_language_from_cookies
from users.schemas import UserDTO

from .facade import IPromotionFacade
from .schemas import GetPromotionTariffsResponse

router = APIRouter(
    prefix="/promotions",
    tags=["promotions"],
)


@router.get("/")
@inject
async def get_promotion_tariffs(
    language: str = Depends(get_language_from_cookies),
    promotion_facade: IPromotionFacade = Depends(Provide[Container.promotion_facade]),
) -> GetPromotionTariffsResponse:
    return await promotion_facade.get_tariffs(language)
