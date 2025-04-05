from core.repositories import BaseRepository
from sqlalchemy import select, func

from items.models import Item
from users.schemas import UserDTO
from items.schemas import ItemDTO, CreateItem, UpdateItem

from fastapi import HTTPException, UploadFile
from PIL import Image
import io
import os
from core.utils import generate_hashed_filename


class ItemRepository(BaseRepository):

    async def get_my_items(
        self, current_user: UserDTO, 
        search: str | None = None, limit: int = 10, 
        offset: int = 0
    ) -> tuple[list[ItemDTO], int]:
        async with self.get_session() as session:
            query = select(Item).filter(Item.shop_id == current_user.id)
            if search:
                query = query.filter(Item.name.ilike(f"%{search}%"))
            items = await session.execute(query.offset(offset).limit(limit))

            count = await session.execute(
                select(
                    func.count(Item.id)
                ).filter(Item.shop_id == current_user.id)
            )
            items = items.scalars().all()
            return [
                ItemDTO.model_validate(item) for item in items
            ], count.scalar()

    async def get_shop_items(
        self, shop_id: int,
        search: str | None = None, 
        limit: int = 10, 
        offset: int = 0
    ) -> tuple[list[ItemDTO], int]:
        async with self.get_session() as session:
            query = select(Item).filter(Item.shop_id == shop_id)
            if search:
                query = query.filter(Item.name.ilike(f"%{search}%"))
            items = await session.execute(query.offset(offset).limit(limit))
            items = items.scalars().all()

            count_query = select(
                select(
                    func.count(Item.id)
                ).filter(Item.shop_id == shop_id)
            )
            if search:
                count_query = count_query.filter(Item.name.ilike(f"%{search}%"))
            count = await session.execute(count_query)
            return [
                ItemDTO.model_validate(item) for item in items
            ], count.scalar()

    async def get_catalog(
        self, 
        search: str | None = None,
        limit: int = 10,
        offset: int = 0
    ) -> tuple[list[ItemDTO], int]:
        async with self.get_session() as session:
            query = select(Item)
            if search:
                query = query.filter(Item.name.ilike(f"%{search}%"))
            items = await session.execute(query.offset(offset).limit(limit))
            items = items.scalars().all()

            count_query = select(
                func.count(Item.id)
            )
            if search:
                count_query = count_query.filter(Item.name.ilike(f"%{search}%"))
            count = await session.execute(count_query)
            
            return [
                ItemDTO.model_validate(item) for item in items
            ], count.scalar()
        
    async def get_my_item(self, item_id: int, current_user: UserDTO) -> ItemDTO:
        async with self.get_session() as session:
            item = await session.execute(
                select(Item).filter(
                    Item.id == item_id, Item.shop_id == current_user.id
                )
            )
            item = item.scalar()
            if item:
                return ItemDTO.model_validate(item)
            raise HTTPException(status_code=404, detail="error.item.not_found")
        
    async def get_item(self, item_id: int) -> ItemDTO | None:
        async with self.get_session() as session:
            item = await session.execute(
                select(Item).filter(Item.id == item_id)
            )
            item = item.scalar()
            if item:
                return ItemDTO.model_validate(item)

    async def _upload_photo(self, user_id: int, photo: UploadFile) -> str:  
        allowed_types = ["image/jpeg", "image/png", "image/heif"]
        if photo.content_type not in allowed_types:
            raise HTTPException(status_code=422, detail="error.photo.invalid_type")

        max_size = 5 * 1024 * 1024
        content = await photo.read()
        file_size = len(content)

        if file_size > max_size:
            image = Image.open(io.BytesIO(content))

            max_dimension = 2000
            quality = 95

            while file_size > max_size and (quality > 20 or max_dimension > 800):
                if max(image.size) > max_dimension:
                    ratio = min(max_dimension / max(image.size[0], image.size[1]), 1.0)
                    new_size = tuple(int(dim * ratio) for dim in image.size)
                    image = image.resize(new_size, Image.Resampling.LANCZOS)

                output = io.BytesIO()
                image.save(output, format="JPEG", quality=quality, optimize=True)
                content = output.getvalue()
                file_size = len(content)

                if file_size > max_size:
                    quality -= 5
                    max_dimension = int(max_dimension * 0.9)

                if file_size > max_size:
                    image = Image.open(io.BytesIO(content))

            if file_size > max_size:
                raise HTTPException(status_code=422, detail="error.photo.too_large")

        os.makedirs("media/items", exist_ok=True)

        hashed_filename = generate_hashed_filename(photo.filename)
        file_location = f"media/items/{user_id}_{hashed_filename}"
        with open(file_location, "wb") as file:
            file.write(content)
        return file_location
    
    async def create_item(
        self, 
        item: CreateItem, 
        current_user: UserDTO,
        photo: UploadFile, 
    ) -> ItemDTO:
        async with self.get_session() as session:
            photo_path = await self._upload_photo(current_user.id, photo)
            item = Item(
                name=item.name,
                description=item.description,
                price=item.price,
                type=item.type,
                shop_id=current_user.id,
                photo=photo_path
            )
            session.add(item)
            await session.commit()
            return ItemDTO.model_validate(item)

    async def update_item(
        self, 
        item_id: int, 
        item: UpdateItem, 
        current_user: UserDTO
    ) -> ItemDTO:
        async with self.get_session() as session:
            item = await session.execute(
                select(Item).filter(Item.id == item_id, Item.shop_id == current_user.id)
            )
            item = item.scalar()
            for field, value in item.model_dump(exclude_none=True).items():
                setattr(item, field, value)
            await session.commit()
            await session.refresh(item)
            return ItemDTO.model_validate(item)
            
    async def update_item_photo(
        self, 
        item_id: int, 
        photo: UploadFile, 
        current_user: UserDTO
    ) -> ItemDTO:
        async with self.get_session() as session:
            item = await session.execute(
                select(Item).filter(Item.id == item_id, Item.shop_id == current_user.id)
            )
            item = item.scalar()
            current_photo = item.photo

            if current_photo:
                os.remove(current_photo)

            photo_path = await self._upload_photo(current_user.id, photo)
            item.photo = photo_path
            await session.commit()
            await session.refresh(item)
            return ItemDTO.model_validate(item)
        
    async def delete_item(
        self, 
        item_id: int, 
        current_user: UserDTO
    ):
        async with self.get_session() as session:
            item = await session.execute(select(Item).filter(Item.id == item_id, Item.shop_id == current_user.id))
            item = item.scalar()
            await session.delete(item)
            await session.commit()