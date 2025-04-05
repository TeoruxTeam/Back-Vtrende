from typing import Optional

import bcrypt

from auth.schemas import SignUpSchema
from core.environment import env
from fastapi import UploadFile
from .repositories import UserRepository
from .schemas import (
    GetMeResponseSchema,
    UserDTO,
    UpdateShop,
    UpdateShopResponseSchema,
    UpdateShopImageResponseSchema
)

class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def create_user(self, schema: SignUpSchema, hashed_password) -> UserDTO:
        
        user: UserDTO = await self.repo.create_user(schema, hashed_password)
        return user

    async def get_user_by_email(
        self, email: str, pwd_required: bool = False,
        is_shop: bool | None = None
    ) -> UserDTO:
        return await self.repo.get_user_by_email(email, pwd_required, is_shop)

    async def verify_password(self, password: str, hashed_password: str) -> bool:
        peppered_password = password + env.secret_key
        return bcrypt.checkpw(
            peppered_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

    async def get_user_by_id(
        self, user_id: int, pwd_required: bool, is_shop: bool | None = None
    ) -> UserDTO:
        return await self.repo.get_user_by_id(user_id, pwd_required, is_shop)

    async def get_me(self, user: UserDTO) -> GetMeResponseSchema:
        return GetMeResponseSchema(data=user)

    async def verify_user(self, user: UserDTO) -> None:
        await self.repo.verify_user(user.id)

    async def get_password_hash(self, password: str) -> str:
        peppered_password = password + env.secret_key
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(peppered_password.encode("utf-8"), salt)
        return hashed_password.decode("utf-8")
    
    async def create_user_oauth(
        self, name: str, email: str, avatar: Optional[str]
    ) -> UserDTO:
        return await self.repo.create_user_oauth(name, email, avatar)

    async def update_shop(
        self, user: UserDTO, payload: UpdateShop
    ) -> UpdateShopResponseSchema:
        shop = await self.repo.update_shop(user, payload)
        return UpdateShopResponseSchema(data=shop)
    
    async def update_shop_photo(
        self, user: UserDTO, photo: UploadFile
    ) -> UpdateShopImageResponseSchema:
        shop = await self.repo.update_shop_photo(user, photo)
        return UpdateShopImageResponseSchema(data=shop)
    