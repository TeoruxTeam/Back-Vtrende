from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class LocationDTO(BaseModel):
    id: int
    latitude: Decimal
    longitude: Decimal
    address: Optional[str]
