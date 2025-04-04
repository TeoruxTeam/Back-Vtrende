import hashlib
import io
import os
import uuid
from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager
from datetime import datetime
from typing import Callable, List, Optional

from fastapi import HTTPException, UploadFile
from PIL import Image
from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from admin.schemas import AdminPatchUserRequest, AdminPUserDataSchema
from auth.schemas import SignUpSchema
from core.logger import logger
from core.repositories import BaseRepository
from core.utils import generate_hashed_filename
from notifications.models import NotificationSettings

from .mappers import UserMapper
from .models import User
from .schemas import PutMeRequestSchema, PutMeResponseSchema, UserDTO


class IUserRepository(ABC):

    @abstractmethod
    async def create_user(self, schema: SignUpSchema, hashed_password: str) -> UserDTO:
        pass

    @abstractmethod
    async def delete_user(self, user_id: int, time_now: datetime) -> None:
        pass

    @abstractmethod
    async def get_user_by_email(
        self, email: str, pwd_required: bool = False
    ) -> UserDTO:
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> UserDTO:
        pass

    @abstractmethod
    async def verify_user(self, user: UserDTO) -> None:
        pass

    @abstractmethod
    async def update_password_by_user_id(self, user_id, new_password: str) -> None:
        pass

    @abstractmethod
    async def update_user(
        self, user: UserDTO, schema: PutMeRequestSchema, photo: UploadFile
    ) -> UserDTO:
        pass

    @abstractmethod
    async def adminp_get_all_users(
        self, limit: int, offset: int
    ) -> List[AdminPUserDataSchema]:
        pass

    @abstractmethod
    async def adminp_get_user_by_id(self, user_id: int) -> AdminPUserDataSchema:
        pass

    @abstractmethod
    async def adminp_edit_user(
        self, user_id: int, schema: AdminPatchUserRequest
    ) -> None:
        pass

    @abstractmethod
    async def adminp_ban_user(self, user_id: int, time_now: datetime) -> None:
        pass

    @abstractmethod
    async def adminp_unban_user(self, user_id: int, time_now: datetime) -> None:
        pass

    @abstractmethod
    async def get_total_users_count(self) -> int:
        pass

    @abstractmethod
    async def get_new_users_count_from_date(self, time_from: datetime) -> int:
        pass

    @abstractmethod
    async def create_user_oauth(
        self, name: str, email: str, avatar: Optional[str]
    ) -> UserDTO:
        pass


class UserRepository(IUserRepository, BaseRepository):

    async def create_user(self, schema: SignUpSchema, hashed_password: str) -> UserDTO:
        async with self.get_session() as session:

            existing_user = await session.execute(
                select(User).where(User.email == schema.email, User.is_deleted == True)
            )
            existing_user = existing_user.scalar()

            if existing_user and existing_user.is_deleted:
                existing_user.name = schema.name
                existing_user.password = hashed_password
                existing_user.is_deleted = False

                await session.flush()

                dto_user = UserMapper.to_dto(existing_user)
            else:
                user = User(
                    name=schema.name,
                    surname=None,
                    email=schema.email,
                    password=hashed_password,
                )
                session.add(user)
                await session.flush()
                await session.refresh(user)
                notification_settings = NotificationSettings(user_id=user.id)
                session.add(notification_settings)
                await session.flush()
                dto_user = UserMapper.to_dto(user)

            await session.commit()

            return dto_user

    async def delete_user(self, user_id: int, time_now: datetime) -> None:
        async with self.get_session() as session:
            query = (
                update(User)
                .where(User.id == user_id)
                .values(is_deleted=True, deleted_at=time_now)
            )
            await session.execute(query)
            await session.commit()

    async def get_user_by_email(
        self, email: str, pwd_required: bool = False
    ) -> Optional[UserDTO]:
        async with self.get_session() as session:
            query = select(User).where(User.email == email, User.is_deleted == False)
            results = await session.execute(query)
            user = results.scalars().first()
            if user:
                return (
                    UserMapper.to_dto_with_pwd(user)
                    if pwd_required
                    else UserMapper.to_dto(user)
                )
            return None

    async def get_user_by_id(self, user_id: int, pwd_required: bool = False) -> UserDTO:
        async with self.get_session() as session:
            logger.info(f"Session id {session}")
            query = select(User).where(User.id == user_id, User.is_deleted == False)
            result = await session.execute(query)
            user = result.scalars().first()
            if user:
                return (
                    UserMapper.to_dto_with_pwd(user)
                    if pwd_required
                    else UserMapper.to_dto(user)
                )
            return None

    async def verify_user(self, user: UserDTO) -> None:
        async with self.get_session() as session:
            query = update(User).where(User.id == user.id).values(is_activated=True)
            await session.execute(query)
            await session.commit()

    async def update_password_by_user_id(self, user_id, new_password: str) -> None:
        async with self.get_session() as session:
            query = update(User).where(User.id == user_id).values(password=new_password)
            await session.execute(query)
            await session.commit()

    async def _upload_photo(self, user_id: int, photo: UploadFile) -> str:
        # Проверка типа файла

        allowed_types = ["image/jpeg", "image/png", "image/heif"]
        if photo.content_type not in allowed_types:
            logger.error(f"Invalid photo type: {photo.content_type}")
            raise HTTPException(status_code=422, detail="error.photo.invalid_type")

        # Проверка размера файла (максимум 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        content = await photo.read()
        file_size = len(content)

        # Если файл больше максимального размера, сжимаем его
        if file_size > max_size:
            image = Image.open(io.BytesIO(content))

            # Начальные параметры
            max_dimension = 2000
            quality = 95

            while file_size > max_size and (quality > 20 or max_dimension > 800):
                # Уменьшаем размер изображения, если оно все еще слишком большое
                if max(image.size) > max_dimension:
                    ratio = min(max_dimension / max(image.size[0], image.size[1]), 1.0)
                    new_size = tuple(int(dim * ratio) for dim in image.size)
                    image = image.resize(new_size, Image.Resampling.LANCZOS)

                # Сжимаем с текущим качеством
                output = io.BytesIO()
                image.save(output, format="JPEG", quality=quality, optimize=True)
                content = output.getvalue()
                file_size = len(content)

                # Если размер все еще большой, уменьшаем качество и размер
                if file_size > max_size:
                    quality -= 5
                    max_dimension = int(max_dimension * 0.9)

                # Переоткрываем изображение для следующей итерации
                if file_size > max_size:
                    image = Image.open(io.BytesIO(content))

            if file_size > max_size:
                raise HTTPException(status_code=422, detail="error.photo.too_large")

        # Создание директории, если она не существует
        os.makedirs("media/avatars", exist_ok=True)

        hashed_filename = generate_hashed_filename(photo.filename)
        file_location = f"media/avatars/{user_id}_{hashed_filename}"
        with open(file_location, "wb") as file:
            file.write(content)
        return file_location

    async def update_user(
        self, user: UserDTO, schema: PutMeRequestSchema, photo: Optional[UploadFile]
    ) -> None:
        async with self.get_session() as session:

            query = (
                update(User)
                .where(User.id == user.id)
                .values(
                    name=schema.name,
                    surname=schema.surname,
                    email=schema.email,
                    phone_number=schema.phone_number,
                )
            )

            if schema.delete_photo:
                if photo:
                    photo_path = (
                        await self._upload_photo(user.id, photo) if photo else None
                    )
                    query = query.values(avatar=photo_path)
                else:
                    query = query.values(avatar=None)

            await session.execute(query)
            await session.commit()

    async def adminp_get_all_users(
        self, limit: int, offset: int
    ) -> List[AdminPUserDataSchema]:
        async with self.get_session() as session:
            query = (
                select(User)
                .where(User.is_admin == False)
                .order_by(User.id.asc())
                .offset(offset)
                .limit(limit)
            )
            count_result = await session.execute(
                select(func.count(User.id)).where(User.is_admin == False)
            )
            results = await session.execute(query)
            count = count_result.scalar()
            users = results.scalars().all()
            return UserMapper.to_adminp_user_data_list(users), count

    async def adminp_get_user_by_id(self, user_id: int) -> AdminPUserDataSchema:
        async with self.get_session() as session:
            query = select(User).where(User.id == user_id, User.is_admin == False)
            result = await session.execute(query)
            user = result.scalars().first()
            if user:
                return UserMapper.to_adminp_user_data(user)
            return None

    async def adminp_edit_user(
        self, user_id: int, schema: AdminPatchUserRequest
    ) -> None:
        async with self.get_session() as session:
            update_data = schema.model_dump(exclude_unset=True)
            query = (
                update(User)
                .where(User.id == user_id, User.is_admin == False)
                .values(**update_data)
            )
            await session.execute(query)
            await session.commit()

    async def adminp_ban_user(self, user_id: int, time_now: datetime) -> None:
        async with self.get_session() as session:
            query = (
                update(User)
                .where(User.id == user_id)
                .values(is_banned=True, banned_at=time_now)
            )
            await session.execute(query)
            await session.commit()

    async def adminp_unban_user(self, user_id: int, time_now: datetime) -> None:
        async with self.get_session() as session:
            query = (
                update(User)
                .where(User.id == user_id)
                .values(is_banned=False, banned_at=time_now)
            )
            await session.execute(query)
            await session.commit()

    async def get_total_users_count(self) -> int:
        async with self.get_session() as session:
            results = await session.execute(
                select(func.count(User.id)).where(User.is_deleted == False)
            )
            total_users = results.scalar()
            return total_users

    async def get_new_users_count_from_date(self, time_from: datetime) -> int:
        async with self.get_session() as session:
            results = await session.execute(
                select(func.count()).where(
                    User.created_at >= time_from,
                    User.is_activated == True,
                )
            )

            new_users_count = results.scalar()
            return new_users_count

    async def create_user_oauth(
        self, name: str, email: str, avatar: Optional[str]
    ) -> UserDTO:
        async with self.get_session() as session:

            existing_user = await session.execute(
                select(User).where(User.email == email, User.is_deleted == True)
            )
            existing_user = existing_user.scalar()

            if existing_user and existing_user.is_deleted:
                existing_user.name = name
                existing_user.password = None
                existing_user.is_deleted = False

                await session.flush()

                dto_user = UserMapper.to_dto(existing_user)
            else:
                user = User(
                    name=name,
                    surname=None,
                    email=email,
                    password=None,
                )
                notification_settings = NotificationSettings(user_id=user.id)
                session.add(user)
                session.add(notification_settings)
                await session.flush()

                dto_user = UserMapper.to_dto(user)

            await session.commit()

            return dto_user
