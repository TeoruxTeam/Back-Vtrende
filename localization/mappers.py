from .models import Localization, LocalizationKey
from .schemas import LocalizationFromORM, LocalizationKeyFromORM


class LocalizationKeyMapper:

    @staticmethod
    def to_localization_key_from_orm(entity: LocalizationKey) -> LocalizationKeyFromORM:
        return LocalizationKeyFromORM(id=entity.id, key=entity.key)


class LocalizationMapper:

    @staticmethod
    def to_localization_from_orm(entity: Localization) -> LocalizationFromORM:
        return LocalizationFromORM(
            id=entity.id,
            localization_key_id=entity.localization_key_id,
            language=entity.language,
            value=entity.value,
        )
