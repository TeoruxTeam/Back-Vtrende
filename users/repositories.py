import io
import os
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, UploadFile
from PIL import Image
from sqlalchemy import update
from sqlalchemy.future import select

from auth.schemas import SignUpSchema
from core.logger import logger
from core.repositories import BaseRepository
from core.utils import generate_hashed_filename

from .models import User
from .schemas import (
    UserDTO, UserWithPasswordDTO,
    UpdateShop,
    UpdateShopResponseSchema,
    UpdateShopImageResponseSchema
)


class UserRepository(BaseRepository):

    async def create_user(
        self, schema: SignUpSchema, hashed_password: str
    ) -> UserDTO:
        async with self.get_session() as session:
            user = User(
                email=schema.email,
                password=hashed_password,
                is_shop=schema.is_shop,
                iin_bin=schema.iin_bin
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            dto_user = UserDTO.model_validate(user)

            return dto_user

    async def get_user_by_email(
        self, email: str, pwd_required: bool = False, 
        is_shop: bool | None = None
    ) -> Optional[UserDTO]:
        async with self.get_session() as session:
            query = select(User).where(
                User.email == email
            )
            if is_shop is not None:
                query = query.where(User.is_shop == is_shop)
            results = await session.execute(query)
            user = results.scalars().first()
            if user:
                if pwd_required:
                    return UserWithPasswordDTO.model_validate(user)
                else:
                    return UserDTO.model_validate(user)
            return None

    async def get_user_by_id(
        self, user_id: int, pwd_required: bool = False, is_shop: bool | None = None
    ) -> Optional[UserDTO]:
        async with self.get_session() as session:
            query = select(User).where(User.id == user_id)
            if is_shop is not None:
                query = query.where(User.is_shop == is_shop)
            results = await session.execute(query)
            user = results.scalars().first()
            if user:
                if pwd_required:
                    return UserWithPasswordDTO.model_validate(user)
                else:
                    return UserDTO.model_validate(user)
            return None

    async def verify_user(self, user_id: int) -> None:
        async with self.get_session() as session:
            query = update(User).where(User.id == user_id).values(verified=True)
            await session.execute(query)
            await session.commit()

    async def update_password_by_user_id(self, user_id: int, new_password: str) -> None:
        async with self.get_session() as session:
            query = update(User).where(User.id == user_id).values(password=new_password)
            await session.execute(query)
            await session.commit()

    async def _upload_photo(self, user_id: int, photo: UploadFile) -> str:  
        allowed_types = ["image/jpeg", "image/png", "image/heif"]
        if photo.content_type not in allowed_types:
            logger.error(f"Invalid photo type: {photo.content_type}")
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

        os.makedirs("media/avatars", exist_ok=True)

        hashed_filename = generate_hashed_filename(photo.filename)
        file_location = f"media/avatars/{user_id}_{hashed_filename}"
        with open(file_location, "wb") as file:
            file.write(content)
        return file_location

    async def create_user_oauth(
        self, email: str, is_shop: bool
    ) -> UserDTO:
        async with self.get_session() as session:

            existing_user = await session.execute(
                select(User).where(User.email == email)
            )
            existing_user = existing_user.scalar()
            user = User(
                email=email,
                is_shop=is_shop,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            dto_user = UserDTO.model_validate(user)

            return dto_user

    async def update_shop(
        self, user: UserDTO, payload: UpdateShop
    ) -> UserDTO:
        async with self.get_session() as session:
            shop = await session.execute(select(User).where(User.id == user.id))
            shop = shop.scalar()
            if shop:
                for key, value in payload.model_dump(exclude_none=True).items():
                    setattr(shop, key, value)
                await session.commit()
                await session.refresh(shop)
                return UserDTO.model_validate(shop)
            raise HTTPException(status_code=404, detail="error.shop.not_found")

    async def update_shop_photo(
        self, user: UserDTO, photo: UploadFile
    ) -> UserDTO:
        async with self.get_session() as session:
            shop = await session.execute(select(User).where(User.id == user.id))
            shop = shop.scalar()
            if shop:
                current_photo = shop.avatar
                if current_photo:
                    os.remove(current_photo)
                shop.avatar = await self._upload_photo(user.id, photo)
                await session.commit()
                await session.refresh(shop)
                return UserDTO.model_validate(shop)
            raise HTTPException(status_code=404, detail="error.shop.not_found")

