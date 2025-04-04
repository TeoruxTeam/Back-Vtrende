from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager
from decimal import Decimal
from typing import Callable, List, Optional, Tuple

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.database import IUnitOfWork
from core.logger import logger
from core.repositories import BaseRepository
from locations.schemas import LocationDTO

from .mappers import LocationMapper
from .models import Location


class ILocationRepository(ABC):

    @abstractmethod
    async def save_location(self, latitude: Decimal, longitude: Decimal) -> str:
        pass

    @abstractmethod
    async def get_address_by_coordinates(
        self, latitude: Decimal, longitude: Decimal
    ) -> str:
        pass

    @abstractmethod
    async def get_locations_without_address(self, limit: int) -> List[LocationDTO]:
        pass

    @abstractmethod
    async def update_location_address(self, batch_data) -> None:
        pass

    @abstractmethod
    async def create_location(
        self, latitude: Decimal, longitude: Decimal, session: Optional[AsyncSession]
    ) -> LocationDTO:
        pass

    @abstractmethod
    async def get_location_by_coordinates(
        self, latitude: Decimal, longitude: Decimal, session: Optional[AsyncSession]
    ) -> Optional[LocationDTO]:
        pass


class LocationRepository(ILocationRepository, BaseRepository):

    async def save_location(self, latitude: Decimal, longitude: Decimal) -> str:
        async with self.session_factory() as session:
            query = Location(latitude=latitude, longitude=longitude)
            session.add(query)
            await session.commit()
            await session.refresh(query)
            return query.id

    async def get_address_by_coordinates(
        self, latitude: Decimal, longitude: Decimal
    ) -> str:
        async with self.session_factory() as session:
            query = (
                select(Location)
                .where(Location.latitude == latitude, Location.longitude == longitude)
                .first()
            )
            location = await session.execute(query)
            if location:
                return location.address
            else:
                return None

    async def get_locations_without_address(self, limit: int) -> List[LocationDTO]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Location)
                .where(Location.address == None)
                .order_by(Location.created_at)
                .limit(limit)
            )
            locations = result.scalars().all()
            if locations:
                return LocationMapper.to_dto_list(locations)
            else:
                return None

    async def update_location_address(self, batch_data: List[Tuple[int, str]]) -> None:
        async with self.session_factory() as session:
            for location_id, address in batch_data:
                query = (
                    update(Location)
                    .where(Location.id == location_id)
                    .values(address=address)
                )
                await session.execute(query)
            await session.commit()

    async def create_location(
        self,
        latitude: Decimal,
        longitude: Decimal,
        external_session: Optional[AsyncSession] = None,
    ) -> LocationDTO:
        async with self.get_session(external_session) as session:
            try:
                logger.info(
                    f"Creating location in session {session} with latitude={latitude}, longitude={longitude}"
                )
                query = Location(latitude=latitude, longitude=longitude)

                session.add(query)

                if external_session:
                    await session.flush()
                else:
                    await session.commit()
                    await session.refresh(query)

                return LocationMapper.to_dto(query)

            except Exception as e:
                logger.error(f"Error while creating location: {e}")
                if session.is_active:  # Ensure the session is rolled back on error
                    await session.rollback()
                raise  # Re-raise the exception after rollback

    async def get_location_by_coordinates(
        self,
        latitude: Decimal,
        longitude: Decimal,
        external_session: Optional[AsyncSession] = None,
    ) -> Optional[LocationDTO]:
        async with self.get_session(external_session) as session:
            query = select(Location).where(
                Location.latitude == latitude, Location.longitude == longitude
            )
            result = await session.execute(query)
            location = result.scalars().first()
            if location:
                return LocationMapper.to_dto(location)
            else:
                return None
