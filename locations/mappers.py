from typing import List

from .models import Location
from .schemas import LocationDTO


class LocationMapper:
    @staticmethod
    def to_dto(location: Location) -> LocationDTO:
        return LocationDTO(
            id=location.id,
            latitude=location.latitude,
            longitude=location.longitude,
            address=location.address,
            created_at=location.created_at,
        )

    @staticmethod
    def to_dto_list(locations: List[Location]) -> List[LocationDTO]:
        return [LocationMapper.to_dto(location) for location in locations]
