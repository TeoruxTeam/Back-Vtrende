from datetime import datetime
from typing import Optional

from pydantic import BaseModel 

from core.schemas import StatusOkSchema


class UserPublicData(BaseModel):
    id: int
    email: str
    is_shop: bool
    verified: bool
    created_at: datetime
    iin_bin: Optional[str] = None
    avatar: Optional[str] = None


class UserDTO(UserPublicData):
    class Config:
        from_attributes = True


class UserWithPasswordDTO(UserDTO):
    password: str


class GetMeResponseSchema(StatusOkSchema):
    data: UserDTO


class UpdateShop(BaseModel):
    name: str
    description: str

class UpdateShopResponseSchema(StatusOkSchema):
    data: UserDTO
    message: str = "success.shop.updated"


class UpdateShopImageResponseSchema(StatusOkSchema):
    data: UserDTO
    message: str = "success.shop.image.updated"
