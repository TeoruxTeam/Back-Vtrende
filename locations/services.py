import asyncio
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import IUnitOfWork
from core.logger import logger
from core.nominatim import geocoder

from .repositories import ILocationRepository
from .schemas import LocationDTO


class ILocationService(ABC):
    def __init__(self, repo: ILocationRepository):
        self.repo = repo

    @abstractmethod
    async def _get_address_by_coordinates(
        self, latitude: float, longitude: float
    ) -> str:
        pass

    @abstractmethod
    async def save_location(
        self, latitude: float, longitude: float, address: str
    ) -> None:
        pass

    @abstractmethod
    async def get_locations_without_address(self, limit) -> List[LocationDTO]:
        pass

    @abstractmethod
    async def update_address_by_coordinates(self, locations: List[LocationDTO]) -> None:
        pass

    @abstractmethod
    async def get_or_create_location(
        self, latitude: Decimal, longitude: Decimal, session: AsyncSession
    ) -> LocationDTO:
        pass


class LocationService(ILocationService):
    def __init__(self, repo: ILocationRepository):
        self.repo = repo

    async def _get_address_by_coordinates(
        self, latitude: float, longitude: float
    ) -> str:
        return await geocoder.reverse_geocode(latitude, longitude)

    async def get_locations_without_address(self, limit) -> List[LocationDTO]:
        return await self.repo.get_locations_without_address(limit)

    async def save_location(
        self, latitude: float, longitude: float, address: str
    ) -> None:
        await self.repo.save_location(latitude, longitude, address)

    async def update_address_by_coordinates(self, locations: List[LocationDTO]) -> None:
        batch_data = []
        for location in locations:
            address = await self._get_address_by_coordinates(
                location.latitude, location.longitude
            )
            batch_data.append((location.id, address))
            await asyncio.sleep(2)
        await self.repo.update_location_address(batch_data)

    async def get_or_create_location(
        self, latitude: Decimal, longitude: Decimal, session: AsyncSession
    ) -> LocationDTO:
        location = await self.repo.get_location_by_coordinates(
            latitude, longitude, session
        )
        if location:
            return location
        return await self.repo.create_location(latitude, longitude, session)
