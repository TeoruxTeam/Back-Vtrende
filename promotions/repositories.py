from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.future import select
from sqlalchemy.orm import aliased

from core.repositories import BaseRepository
from listings.models import Listing
from localization.models import Localization, LocalizationKey

from .mappers import PromotionMapper
from .models import PromotionOrder, PromotionTariff
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


class IPromotionRepository(ABC, BaseRepository):

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
    ) -> CreateTariffResponse:
        pass

    @abstractmethod
    async def delete_tariff(self, tariff_id: int) -> None:
        pass

    @abstractmethod
    async def update_tariff(
        self, tariff_id: int, payload: UpdateTariffRequest
    ) -> UpdateTariffResponse:
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
    async def get_pendings_to_cancel(self, limit_date: datetime) -> list[int]:
        pass

    @abstractmethod
    async def get_orders(
        self, user_id: int, limit: int, offset: int
    ) -> tuple[list[PromotionOrderDTO], int]:
        pass


class PromotionRepository(IPromotionRepository):

    async def add_order(self, listing_id: int, tariff_id: int) -> int:
        async with self.get_session() as session:
            new_order = PromotionOrder(
                listing_id=listing_id,
                tariff_id=tariff_id,
                status="PENDING",
            )
            session.add(new_order)
            await session.commit()
            await session.refresh(new_order)
            return new_order.id

    async def get_tariff(
        self, tariff_id: int, language: Optional[str] = "en"
    ) -> Optional[PromotionTariffDTOWithLocalization]:
        async with self.get_session() as session:
            name_localization = aliased(Localization)
            description_localization = aliased(Localization)

            # Alias the LocalizationKey table for name and description
            name_localization_key = aliased(LocalizationKey)
            description_localization_key = aliased(LocalizationKey)

            query = (
                select(
                    PromotionTariff,
                    name_localization.value.label("name"),
                    description_localization.value.label("description"),
                )
                .join(
                    name_localization_key,
                    PromotionTariff.name_localization_key_id
                    == name_localization_key.id,
                )
                .join(
                    name_localization,
                    name_localization.localization_key_id == name_localization_key.id,
                )
                .join(
                    description_localization_key,
                    PromotionTariff.description_localization_key_id
                    == description_localization_key.id,
                )
                .join(
                    description_localization,
                    description_localization.localization_key_id
                    == description_localization_key.id,
                )
                .where(PromotionTariff.id == tariff_id)
                .where(name_localization.language == language)
                .where(description_localization.language == language)
            )

            # Execute the query
            result = await session.execute(query)
            data = result.first()

            if data:
                tariff, name, description = data
                # Return DTO with localized name and description
                return PromotionMapper.to_tariff_dto_with_localization(
                    tariff, name=name, description=description
                )

            return None

    async def get_tariffs(
        self, language: str
    ) -> list[PromotionTariffDTOWithLocalization]:
        async with self.get_session() as session:
            result = await session.execute(
                select(
                    PromotionTariff,
                    Localization.value.label("localized_name"),
                    Localization.value.label("localized_description"),
                )
                .join(
                    LocalizationKey,
                    PromotionTariff.name_localization_key_id == LocalizationKey.id,
                )
                .join(
                    Localization,
                    and_(
                        Localization.localization_key_id == LocalizationKey.id,
                        Localization.language == language,
                    ),
                    isouter=True,
                )
                .filter(PromotionTariff.is_deleted == False)
                .order_by(PromotionTariff.priority)
            )
            rows = result.fetchall()

            tariffs = [
                PromotionMapper.to_tariff_dto_with_localization(
                    tariff, name, description
                )
                for tariff, name, description in rows
            ]
            return tariffs

    async def create_tariff(
        self,
        payload: CreateTariffRequest,
        name_localization_key_id: int,
        description_localization_key_id: int,
    ) -> PromotionTariffDTO:
        async with self.get_session() as session:
            tariff = PromotionTariff(
                name_localization_key_id=name_localization_key_id,
                price=payload.price,
                duration_days=payload.duration_days,
                description_localization_key_id=description_localization_key_id,
                priority=payload.priority,
            )
            session.add(tariff)
            await session.commit()
            await session.refresh(tariff)

            return PromotionMapper.to_tariff_dto(tariff)

    async def delete_tariff(self, tariff_id: int) -> None:
        async with self.get_session() as session:
            tariff = await session.get(PromotionTariff, tariff_id)
            tariff.is_deleted = True
            await session.commit()

    async def update_tariff(
        self, tariff_id: int, payload: UpdateTariffRequest
    ) -> PromotionTariffDTO | ValueError:
        async with self.get_session() as session:
            tariff = await session.get(PromotionTariff, tariff_id)
            if tariff:
                for key, value in payload.dict().items():
                    setattr(tariff, key, value)
                await session.commit()
                await session.refresh(tariff)
                return PromotionMapper.to_tariff_dto(tariff)
            return ValueError("Tariff not found")

    async def get_order(self, order_id: int) -> Optional[PromotionOrderDTO]:
        async with self.get_session() as session:
            order = await session.get(PromotionOrder, order_id)
            if order:
                return PromotionMapper.to_order_dto(order)
            return None

    async def confirm_order(
        self, order_id: int, start_date: datetime, end_date: datetime
    ) -> None:
        async with self.get_session() as session:
            order = await session.get(PromotionOrder, order_id)
            order.status = "PAID"
            order.start_date = start_date
            order.end_date = end_date
            await session.commit()

    async def cancel_order(self, order_id: int) -> None:
        async with self.get_session() as session:
            order = await session.get(PromotionOrder, order_id)
            order.status = "CANCELLED"
            await session.commit()

    async def get_pendings_to_cancel(self, limit_date: datetime) -> list[int]:
        async with self.get_session() as session:
            result = await session.execute(
                select(PromotionOrder.id)
                .filter(PromotionOrder.status == "PENDING")
                .filter(PromotionOrder.created_at < limit_date)
            )
            return [row[0] for row in result]

    async def get_orders(
        self, user_id: int, limit: int, offset: int
    ) -> tuple[list[PromotionOrderDTO], int]:
        async with self.get_session() as session:
            result = await session.execute(
                select(PromotionOrder)
                .join(Listing, PromotionOrder.listing_id == Listing.id)
                .filter(Listing.user_id == user_id)
                .limit(limit)
                .offset(offset)
            )
            orders = result.scalars().all()

            count_result = await session.execute(
                select(func.count(PromotionOrder.id))
                .join(Listing, PromotionOrder.listing_id == Listing.id)
                .filter(Listing.user_id == user_id)
            )
            count = count_result.scalar()
            return [PromotionMapper.to_order_dto(order) for order in orders], count
