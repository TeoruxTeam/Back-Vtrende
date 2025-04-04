from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

import bcrypt
from fastapi import UploadFile, HTTPException

from admin.schemas import AdminPatchUserRequest, AdminPUserDataSchema
from auth.schemas import SignUpSchema
from core.environment import env
from core.utils import get_media_url

from .exceptions import InvalidPassword, UserNotFound
from .repositories import IUserRepository
from .schemas import (
    GetMeResponseSchema,
    PatchPasswordRequestSchema,
    PatchPasswordResponseSchema,
    PutMeRequestSchema,
    PutMeResponseSchema,
    UserDTO,
)


class IUserService(ABC):

    @abstractmethod
    async def create_user(self, schema: SignUpSchema, hashed_password: str) -> UserDTO:
        pass

    @abstractmethod
    async def delete_user(self, user_id: str) -> None:
        pass

    @abstractmethod
    async def get_user_by_email(
        self, email: str, pwd_required: bool = False
    ) -> UserDTO:
        pass

    @abstractmethod
    async def verify_password(self, password: str, hashed_password: str) -> bool:
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: int, pwd_required: bool) -> UserDTO:
        pass

    @abstractmethod
    async def get_me(self, user: UserDTO, base_url: str) -> GetMeResponseSchema:
        pass

    @abstractmethod
    async def verify_user(self, user: UserDTO) -> None:
        pass

    @abstractmethod
    async def get_password_hash(self, password: str) -> str:
        pass

    @abstractmethod
    async def update_password_by_user_id(self, user_id: int, new_password: str) -> None:
        pass

    @abstractmethod
    async def put_me(
        self,
        schema: PutMeRequestSchema,
        photo: UploadFile,
        user: UserDTO,
        base_url: str,
    ) -> PutMeResponseSchema:
        pass

    @abstractmethod
    async def patch_password(
        self, schema: PatchPasswordRequestSchema, user: UserDTO
    ) -> PatchPasswordResponseSchema:
        pass

    @abstractmethod
    async def adminp_get_all_users(
        self, base_url: str, limit: int, offset: int
    ) -> Tuple[List[AdminPUserDataSchema], int]:
        pass

    @abstractmethod
    async def adminp_get_user_by_id(
        self, user_id: int, base_url: str
    ) -> AdminPUserDataSchema:
        pass

    @abstractmethod
    async def adminp_edit_user(
        self, user_id: int, schema: AdminPatchUserRequest
    ) -> None:
        pass

    @abstractmethod
    async def adminp_ban_user(self, user_id: int) -> None:
        pass

    @abstractmethod
    async def adminp_unban_user(self, user_id: int) -> None:
        pass

    @abstractmethod
    async def get_total_users_count(self) -> int:
        pass

    @abstractmethod
    async def get_new_users_month(self) -> int:
        pass

    @abstractmethod
    async def get_new_users_day(self) -> int:
        pass

    @abstractmethod
    async def create_user_oauth(
        self, name: str, email: str, avatar: Optional[str]
    ) -> UserDTO:
        pass


class UserService(IUserService):
    def __init__(self, repo: IUserRepository):
        self.repo = repo

    async def create_user(self, schema: SignUpSchema, hashed_password) -> UserDTO:
        
        user: UserDTO = await self.repo.create_user(schema, hashed_password)
        return user

    async def delete_user(self, user_id: str) -> None:
        time_now = datetime.now(timezone.utc)
        await self.repo.delete_user(user_id, time_now)

    async def get_user_by_email(
        self, email: str, pwd_required: bool = False
    ) -> UserDTO:
        return await self.repo.get_user_by_email(email, pwd_required)

    async def verify_password(self, password: str, hashed_password: str) -> bool:
        peppered_password = password + env.secret_key
        return bcrypt.checkpw(
            peppered_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

    async def get_user_by_id(self, user_id: int, pwd_required: bool) -> UserDTO:
        return await self.repo.get_user_by_id(user_id, pwd_required)

    async def get_me(self, user: UserDTO, base_url: str) -> GetMeResponseSchema:
        if user.avatar:
            user.avatar = get_media_url(base_url, user.avatar)
        return GetMeResponseSchema(data=user)

    async def verify_user(self, user: UserDTO) -> None:
        await self.repo.verify_user(user)

    async def get_password_hash(self, password: str) -> str:
        peppered_password = password + env.secret_key
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(peppered_password.encode("utf-8"), salt)
        return hashed_password.decode("utf-8")

    async def update_password_by_user_id(self, user_id: int, new_password: str) -> None:
        await self.repo.update_password_by_user_id(user_id, new_password)

    async def put_me(
        self,
        schema: PutMeRequestSchema,
        photo: UploadFile,
        user: UserDTO,
        base_url: str,
    ) -> PutMeResponseSchema:
        if "." in schema.name:
            raise HTTPException(status_code=400, detail="error.user.name_has_dots")
        elif "." in schema.surname:
            raise HTTPException(status_code=400, detail="error.user.surname_has_dots")
        
        if photo:
            schema.delete_photo = True
        await self.repo.update_user(user, schema, photo)
        data = await self.get_user_by_id(user.id, False)
        if data.avatar:
            data.avatar = get_media_url(base_url, data.avatar)
        return PutMeResponseSchema(data=data)

    async def patch_password(
        self, schema: PatchPasswordRequestSchema, user: UserDTO
    ) -> PatchPasswordResponseSchema:
        if not await self.verify_password(schema.old_password, user.password):
            raise InvalidPassword()
        hashed_password = await self.get_password_hash(schema.new_password)
        await self.repo.update_password_by_user_id(user.id, hashed_password)
        return PatchPasswordResponseSchema()

    async def adminp_get_all_users(
        self, base_url: str, limit: int, offset: int
    ) -> List[UserDTO]:
        users, count = await self.repo.adminp_get_all_users(limit, offset)
        for user in users:
            if user.avatar:
                user.avatar = get_media_url(base_url, user.avatar)
        return users, count

    async def adminp_get_user_by_id(
        self, user_id: int, base_url: str
    ) -> AdminPUserDataSchema:
        user = await self.repo.adminp_get_user_by_id(user_id)
        if user:
            if user.avatar:
                user.avatar = get_media_url(base_url, user.avatar)
            return user

        raise UserNotFound()

    async def adminp_edit_user(
        self, user_id: int, schema: AdminPatchUserRequest
    ) -> None:
        await self.repo.adminp_edit_user(user_id, schema)

    async def adminp_ban_user(self, user_id: int) -> None:
        time_now = datetime.now(timezone.utc)
        await self.repo.adminp_ban_user(user_id, time_now)

    async def adminp_unban_user(self, user_id: int) -> None:
        time_now = datetime.now(timezone.utc)
        await self.repo.adminp_unban_user(user_id, time_now)

    async def get_total_users_count(self) -> int:
        return await self.repo.get_total_users_count()

    async def get_new_users_month(self) -> int:
        time_from = datetime.now(timezone.utc) - timedelta(days=30)
        return await self.repo.get_new_users_count_from_date(time_from)

    async def get_new_users_day(self) -> int:
        time_from = datetime.now(timezone.utc) - timedelta(days=1)
        return await self.repo.get_new_users_count_from_date(time_from)

    async def create_user_oauth(
        self, name: str, email: str, avatar: Optional[str]
    ) -> UserDTO:
        return await self.repo.create_user_oauth(name, email, avatar)
