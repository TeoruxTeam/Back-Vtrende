from .models import PromotionOrder, PromotionTariff
from .schemas import (
    PromotionOrderDTO,
    PromotionTariffDTO,
    PromotionTariffDTOWithLocalization,
)


class PromotionMapper:

    @staticmethod
    def to_tariff_dto(tariff: PromotionTariff) -> PromotionTariffDTO:
        return PromotionTariffDTO(
            id=tariff.id,
            name_localization_key_id=tariff.name_localization_key_id,
            price=tariff.price,
            duration_days=tariff.duration_days,
            description_localization_key_id=tariff.description_localization_key_id,
            priority=tariff.priority,
            created_at=tariff.created_at,
        )

    @staticmethod
    def to_tariff_dto_with_localization(
        tariff: PromotionTariff, name: str, description: str
    ) -> PromotionTariffDTOWithLocalization:
        return PromotionTariffDTOWithLocalization(
            id=tariff.id,
            name=name,
            price=tariff.price,
            duration_days=tariff.duration_days,
            description=description,
            priority=tariff.priority,
            created_at=tariff.created_at,
        )

    @staticmethod
    def to_order_dto(order: PromotionOrder) -> PromotionOrderDTO:
        return PromotionOrderDTO(
            id=order.id,
            listing_id=order.listing_id,
            tariff_id=order.tariff_id,
            status=order.status,
            created_at=order.created_at,
        )
