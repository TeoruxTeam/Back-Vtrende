from items.schemas import (
    ItemDTO, CreateItem, UpdateItem, 
    GetMyItemsResponseSchema, GetMyItemResponseSchema, 
    CreateItemResponseSchema, UpdateItemResponseSchema,
    GetItemsResponseSchema, GetCatalogResponseSchema,
    GetItemResponseSchema
)
from items.repositories import ItemRepository
from users.schemas import UserDTO

from fastapi import UploadFile, HTTPException
class ItemService:
    def __init__(self, item_repository: ItemRepository):
        self.item_repository = item_repository

    async def get_my_items(
        self, 
        current_user: UserDTO, search: str | None = None, 
        limit: int = 10, offset: int = 0
    ) -> GetMyItemsResponseSchema:
        items, count = await self.item_repository.get_my_items(
            current_user, search, limit, offset
        )
        return GetMyItemsResponseSchema(data=items, count=count)

    async def get_shop_items(
        self, 
        shop_id: int, 
        search: str | None = None, 
        limit: int = 10, 
        offset: int = 0
    ) -> GetItemsResponseSchema:
        items, count = await self.item_repository.get_shop_items(
            shop_id, search, limit, offset
        )
        return GetItemsResponseSchema(data=items, count=count)
    
    async def get_catalog(
        self, 
        search: str | None = None,
        limit: int = 10,
        offset: int = 0
    ) -> GetCatalogResponseSchema:
        items, count = await self.item_repository.get_catalog(search, limit, offset)
        return GetCatalogResponseSchema(data=items, count=count)

    async def get_my_item(
        self, 
        item_id: int, 
        current_user: UserDTO
    ) -> GetMyItemResponseSchema:
        item = await self.item_repository.get_my_item(item_id, current_user)
        if item:
            return GetMyItemResponseSchema(data=item)
        raise HTTPException(status_code=404, detail="error.item.not_found")
    
    async def get_item(
        self, 
        item_id: int
    ) -> GetItemResponseSchema:
        item = await self.item_repository.get_item(item_id)
        if item:
            return GetItemResponseSchema(data=item)
        raise HTTPException(status_code=404, detail="error.item.not_found")

    async def create_item(
        self, 
        item: CreateItem, 
        current_user: UserDTO,
        photo: UploadFile
    ) -> CreateItemResponseSchema:
        item = await self.item_repository.create_item(item, current_user, photo)
        return CreateItemResponseSchema(data=item)
    
    async def update_item(
        self, 
        item_id: int, 
        item: UpdateItem, 
        current_user: UserDTO
    ) -> UpdateItemResponseSchema:
        item = await self.item_repository.update_item(item_id, item, current_user)
        return UpdateItemResponseSchema(data=item)
    
    async def update_item_photo(
        self, 
        item_id: int, 
        photo: UploadFile, 
        current_user: UserDTO
    ) -> UpdateItemResponseSchema:
        item = await self.item_repository.update_item_photo(item_id, photo, current_user)
        return UpdateItemResponseSchema(data=item)

    async def delete_item(
        self, 
        item_id: int, 
        current_user: UserDTO
    ):
        await self.item_repository.delete_item(item_id, current_user)