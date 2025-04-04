from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from core.schemas import CountSchema, StatusOkSchema


class PromotionTariffDTO(BaseModel):
    id: int
    name_localization_key_id: int
    price: float
    duration_days: int
    description_localization_key_id: int
    priority: int
    created_at: datetime


class CreateTariffRequest(BaseModel):
    name_localization_key: str
    price: float
    duration_days: int
    description_localization_key: str
    priority: int


class UpdateTariffRequest(BaseModel):
    price: float
    duration_days: int
    priority: int


class CreateTariffResponse(StatusOkSchema):
    data: PromotionTariffDTO


class UpdateTariffResponse(StatusOkSchema):
    data: PromotionTariffDTO


class PromotionOrderDTO(BaseModel):
    id: int
    listing_id: int
    tariff_id: int
    status: str
    created_at: datetime


class PromotionTariffDTOWithLocalization(BaseModel):
    id: int
    name: Optional[str]
    price: float
    duration_days: int
    description: Optional[str]
    priority: int
    created_at: datetime


class GetPromotionTariffsResponse(StatusOkSchema):
    data: list[PromotionTariffDTOWithLocalization]
