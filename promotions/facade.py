from abc import ABC, abstractmethod

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from localization.services import ILocalizationKeyService

from .schemas import (
    CreateTariffRequest,
    CreateTariffResponse,
    GetPromotionTariffsResponse,
    UpdateTariffRequest,
    UpdateTariffResponse,
)
from .services import IPromotionService


class IPromotionFacade(ABC):

    @abstractmethod
    async def get_tariffs(self, language: str = "en") -> GetPromotionTariffsResponse:
        pass

    @abstractmethod
    async def create_tariff(self, payload: CreateTariffRequest) -> CreateTariffResponse:
        pass

    @abstractmethod
    async def delete_tariff(self, tariff_id: int) -> None:
        pass

    @abstractmethod
    async def update_tariff(
        self, tariff_id: int, payload: UpdateTariffRequest
    ) -> UpdateTariffResponse:
        pass


class PromotionFacade(IPromotionFacade):

    def __init__(
        self,
        promotion_service: IPromotionService,
        localization_key_service: ILocalizationKeyService,
    ):
        self._promotion_service = promotion_service
        self._localization_key_service = localization_key_service

    async def get_tariffs(self, language: str = "en") -> GetPromotionTariffsResponse:
        tariffs = await self._promotion_service.get_tariffs(language)
        return GetPromotionTariffsResponse(data=tariffs)

    async def create_tariff(self, payload: CreateTariffRequest) -> CreateTariffResponse:
        try:
            name_localization_key = await self._localization_key_service.create(
                payload.name_localization_key
            )
            description_localization_key = await self._localization_key_service.create(
                payload.description_localization_key
            )

            tariff = await self._promotion_service.create_tariff(
                payload, name_localization_key.id, description_localization_key.id
            )
            return CreateTariffResponse(data=tariff)
        except IntegrityError:
            raise HTTPException(
                status_code=400, detail="error.promotion_tariff.already_exists"
            )

    async def delete_tariff(self, tariff_id: int) -> None:
        await self._promotion_service.delete_tariff(tariff_id)

    async def update_tariff(
        self, tariff_id: int, payload: UpdateTariffRequest
    ) -> UpdateTariffResponse | HTTPException:
        try:
            tariff = await self._promotion_service.update_tariff(tariff_id, payload)
            return UpdateTariffResponse(data=tariff)
        except ValueError:
            raise HTTPException(
                status_code=404, detail="error.promotion_tariff.not_found"
            )
