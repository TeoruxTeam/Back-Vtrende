from abc import ABC, abstractmethod
from typing import Optional, Tuple

from sqlalchemy import delete, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.repositories import BaseRepository

from .mappers import LocalizationKeyMapper, LocalizationMapper
from .models import Localization, LocalizationKey
from .schemas import LocalizationFromORM, LocalizationKeyFromORM


class ILocalizationKeyRepository(ABC):

    @abstractmethod
    async def get_by_key(self, key: str):
        pass

    @abstractmethod
    async def create(
        self, key: str, external_session: Optional[AsyncSession]
    ) -> LocalizationKeyFromORM:
        pass

    @abstractmethod
    async def update_by_id(self, id: int, key: str):
        pass

    @abstractmethod
    async def delete_by_id(self, id: int, external_session: Optional[AsyncSession]):
        pass

    @abstractmethod
    async def get_all(
        self, limit: int, offset: int
    ) -> Tuple[LocalizationKeyFromORM, int]:
        pass


class LocalizationKeyRepository(ILocalizationKeyRepository, BaseRepository):

    async def get_by_key(self, key: str) -> LocalizationKeyFromORM:
        async with self.get_session() as session:
            results = await session.execute(
                select(LocalizationKey).where(LocalizationKey.key == key)
            )
            entity = results.scalar()
            return (
                LocalizationKeyMapper.to_localization_key_from_orm(entity)
                if entity
                else None
            )

    async def create(
        self, key: str, external_session: Optional[AsyncSession]
    ) -> LocalizationKeyFromORM:
        async with self.get_session(external_session) as session:
            entity = LocalizationKey(key=key)
            session.add(entity)
            if external_session:
                await session.flush()
            else:
                await session.commit()
                await session.refresh(entity)

            return LocalizationKeyMapper.to_localization_key_from_orm(entity)

    async def update_by_id(self, id: int, key: str):
        async with self.get_session() as session:
            await session.execute(
                update(LocalizationKey).where(LocalizationKey.id == id).values(key=key)
            )
            await session.commit()

    async def delete_by_id(self, id: int, external_session: Optional[AsyncSession]):
        async with self.get_session(external_session) as session:
            await session.execute(
                delete(LocalizationKey).where(LocalizationKey.id == id)
            )
            if not external_session:
                await session.commit()
            else:
                await session.flush()

    async def get_all(
        self, limit: int, offset: int
    ) -> Tuple[LocalizationKeyFromORM, int]:
        async with self.get_session() as session:
            results = await session.execute(
                select(LocalizationKey).limit(limit).offset(offset)
            )
            entities = results.scalars().all()
            count_result = await session.execute(select(func.count(LocalizationKey.id)))
            count = count_result.scalar()
            return [
                LocalizationKeyMapper.to_localization_key_from_orm(entity)
                for entity in entities
            ], count


class ILocalizationRepository(ABC):

    @abstractmethod
    async def get_values_by_key_id(self, key_id: int) -> LocalizationFromORM:
        pass

    @abstractmethod
    async def create(
        self, key_id: int, language: str, value: str
    ) -> LocalizationFromORM:
        pass

    @abstractmethod
    async def update_language_value_by_id(
        self, id: int, value: str
    ) -> LocalizationFromORM:
        pass

    @abstractmethod
    async def delete_by_id(self, id: int) -> None:
        pass


class LocalizationRepository(ILocalizationRepository, BaseRepository):

    async def get_values_by_key_id(self, key_id: int) -> LocalizationFromORM:
        async with self.get_session() as session:
            results = await session.execute(
                select(Localization).where(Localization.localization_key_id == key_id)
            )
            entities = results.scalars().all()
            return [
                LocalizationMapper.to_localization_from_orm(entity)
                for entity in entities
            ]

    async def create(
        self, key_id: int, language: str, value: str
    ) -> LocalizationFromORM:
        async with self.get_session() as session:
            entity = Localization(
                localization_key_id=key_id, language=language, value=value
            )
            session.add(entity)
            await session.commit()
            await session.refresh(entity)
            return LocalizationMapper.to_localization_from_orm(entity)

    async def update_language_value_by_id(
        self, id: int, value: str
    ) -> LocalizationFromORM:
        async with self.get_session() as session:
            result = await session.execute(
                update(Localization)
                .where(Localization.id == id)
                .values(value=value)
                .returning(Localization)
            )
            updated_localization = result.scalar_one()
            await session.commit()
            await session.refresh(updated_localization)
            return LocalizationMapper.to_localization_from_orm(updated_localization)

    async def delete_by_id(self, id: int) -> None:
        async with self.get_session() as session:
            await session.execute(delete(Localization).where(Localization.id == id))
            await session.commit()
