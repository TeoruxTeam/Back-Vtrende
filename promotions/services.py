from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Optional

from .repositories import IPromotionRepository
from .schemas import (
    CreateTariffRequest,
    CreateTariffResponse,
    GetPromotionTariffsResponse,
    PromotionOrderDTO,
    PromotionTariffDTO,
    PromotionTariffDTOWithLocalization,
    UpdateTariffRequest,
    UpdateTariffResponse,
)


class IPromotionService(ABC):

    @abstractmethod
    async def add_order(self, listing_id: int, tariff_id: int) -> int:
        pass

    @abstractmethod
    async def get_tariff(
        self, tariff_id: int, language: Optional[str] = "en"
    ) -> Optional[PromotionTariffDTOWithLocalization]:
        pass

    @abstractmethod
    async def get_tariffs(
        self, language: str
    ) -> list[PromotionTariffDTOWithLocalization]:
        pass

    @abstractmethod
    async def create_tariff(
        self,
        payload: CreateTariffRequest,
        name_localization_key_id: int,
        description_localization_key_id: int,
    ) -> PromotionTariffDTO:
        pass

    @abstractmethod
    async def delete_tariff(self, tariff_id: int) -> None:
        pass

    @abstractmethod
    async def update_tariff(
        self, tariff_id: int, payload: UpdateTariffRequest
    ) -> PromotionTariffDTO | ValueError:
        pass

    @abstractmethod
    async def get_order(self, order_id: int) -> Optional[PromotionOrderDTO]:
        pass

    @abstractmethod
    async def confirm_order(
        self, order_id: int, start_date: datetime, end_date: datetime
    ) -> None:
        pass

    @abstractmethod
    async def cancel_order(self, order_id: int) -> None:
        pass

    @abstractmethod
    async def calculate_end_date(self, tariff_id: int) -> datetime:
        pass

    @abstractmethod
    async def get_orders(
        self, user_id: int, limit: int, offset: int
    ) -> tuple[list[PromotionOrderDTO], int]:
        pass


class PromotionService(IPromotionService):

    def __init__(self, promotion_repository: IPromotionRepository):
        self._promotion_repository = promotion_repository

    async def add_order(self, listing_id: int, tariff_id: int) -> int:
        return await self._promotion_repository.add_order(listing_id, tariff_id)

    async def get_tariff(
        self, tariff_id: int, language: Optional[str] = "en"
    ) -> Optional[PromotionTariffDTOWithLocalization]:
        return await self._promotion_repository.get_tariff(tariff_id, language)

    async def get_tariffs(
        self, language: str
    ) -> list[PromotionTariffDTOWithLocalization]:
        return await self._promotion_repository.get_tariffs(language)

    async def create_tariff(
        self,
        payload: CreateTariffRequest,
        name_localization_key_id: int,
        description_localization_key_id: int,
    ) -> PromotionTariffDTO:
        return await self._promotion_repository.create_tariff(
            payload, name_localization_key_id, description_localization_key_id
        )

    async def delete_tariff(self, tariff_id: int) -> None:
        await self._promotion_repository.delete_tariff(tariff_id)

    async def update_tariff(
        self, tariff_id: int, payload: UpdateTariffRequest
    ) -> PromotionTariffDTO | ValueError:
        return await self._promotion_repository.update_tariff(tariff_id, payload)

    async def get_order(self, order_id: int) -> Optional[PromotionOrderDTO]:
        return await self._promotion_repository.get_order(order_id)

    async def confirm_order(
        self, order_id: int, start_date: datetime, end_date: datetime
    ) -> None:
        await self._promotion_repository.confirm_order(order_id, start_date, end_date)

    async def cancel_order(self, order_id: int) -> None:
        await self._promotion_repository.cancel_order(order_id)

    async def cancel_orders(self, order_ids: list[int]) -> None:
        await self._promotion_repository.cancel_orders(order_ids)

    async def calculate_end_date(self, tariff_id: int) -> datetime:
        tariff = await self._promotion_repository.get_tariff(tariff_id)
        if not tariff:
            raise ValueError("Tariff not found")
        return datetime.now(timezone.utc) + timedelta(days=tariff.duration_days)

    async def get_pendings_to_cancel(self) -> list[int]:
        limit_date = datetime.now(timezone.utc) - timedelta(days=1)
        order_ids = await self._promotion_repository.get_pendings_to_cancel(limit_date)
        return order_ids

    async def get_orders(
        self, user_id: int, limit: int, offset: int
    ) -> tuple[list[PromotionOrderDTO], int]:
        return await self._promotion_repository.get_orders(user_id, limit, offset)
