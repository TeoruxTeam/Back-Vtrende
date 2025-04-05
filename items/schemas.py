from core.schemas import CountSchema, StatusOkSchema
from pydantic import BaseModel, ConfigDict


class ItemDTO(BaseModel):
    id: int
    name: str
    description: str
    price: float
    photo: str
    type: str
    shop_id: int

    model_config = ConfigDict(from_attributes=True)
    


class CreateItem(BaseModel):
    name: str
    description: str
    price: float
    type: str


class UpdateItem(BaseModel):
    name: str
    description: str
    price: float
    type: str
    

class GetMyItemsResponseSchema(StatusOkSchema, CountSchema):
    data: list[ItemDTO]


class GetMyItemResponseSchema(StatusOkSchema):
    data: ItemDTO


class CreateItemResponseSchema(StatusOkSchema):
    data: ItemDTO
    message: str = "success.item.created"


class UpdateItemResponseSchema(StatusOkSchema):
    data: ItemDTO
    message: str = "success.item.updated"


class GetItemsResponseSchema(StatusOkSchema, CountSchema):
    data: list[ItemDTO]


class GetCatalogResponseSchema(StatusOkSchema, CountSchema):
    data: list[ItemDTO]


class GetItemResponseSchema(StatusOkSchema):
    data: ItemDTO