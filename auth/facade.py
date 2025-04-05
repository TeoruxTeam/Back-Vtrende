from abc import ABC, abstractmethod
from datetime import datetime, timezone

import jwt
import httpx
from fastapi import HTTPException
from core.logger import logger
from core.environment import env
from core.exceptions import AuthError
from users.schemas import UserDTO
from users.services import UserService

from .exceptions import InvalidCredentials, UserAlreadyExists
from .schemas import (
    AuthTokensSchema,
    RefreshTokenDTO,
    RefreshTokenRequestSchema,
    RefreshTokenResponseSchema,
    SignInResponseSchema,
    SignInSchema,
    SignUpResponseSchema,
    SignUpSchema,
)
from .services import AuthService


class AuthFacade:
    def __init__(self, user_service: UserService, auth_service: AuthService):
        self.user_service = user_service
        self.auth_service = auth_service

    async def sign_up(self, schema: SignUpSchema) -> SignUpResponseSchema:
        existing_user = await self.user_service.get_user_by_email(schema.email)
        if existing_user:
            raise UserAlreadyExists()
        
        hashed_password = await self.user_service.get_password_hash(schema.password)
        created_user: UserDTO = await self.user_service.create_user(
            schema, hashed_password
        )
        tokens: AuthTokensSchema = await self.auth_service.generate_tokens(
            created_user
        )

        return SignUpResponseSchema(data=tokens)

    async def sign_in(self, schema: SignInSchema) -> SignInResponseSchema:
        logger.info(f"schema: {schema}")
        user = await self.user_service.get_user_by_email(
            schema.email, pwd_required=True
        )
        logger.info(f"user: {user}")
        if not user or not await self.user_service.verify_password(
            schema.password, user.password
        ):
            raise InvalidCredentials()

        tokens: AuthTokensSchema = await self.auth_service.generate_tokens(
            user
        )

        return SignInResponseSchema(data=tokens)

    async def sign_out(self, token: RefreshTokenRequestSchema) -> None:
        await self.auth_service.delete_refresh_token_by_token(token.refresh_token)
        return None

    async def refresh_token(self, token: RefreshTokenRequestSchema) -> AuthTokensSchema:
        refresh_token_record: RefreshTokenDTO = (
            await self.auth_service.get_refresh_token(token.refresh_token)
        )

        if not refresh_token_record:
            raise AuthError(detail="error.auth.token.invalid")

        if refresh_token_record.expiration < datetime.now(timezone.utc):
            raise HTTPException(detail="error.auth.refresh.expired", status_code=401)

        payload = jwt.decode(
            token.refresh_token, env.secret_key, algorithms=[env.jwt_algorithm]
        )
        user_id = int(payload["user_id"])

        user: UserDTO = await self.user_service.get_user_by_id(user_id, False)
        if not user:
            raise AuthError(detail="error.auth.user.not_found")

        await self.auth_service.delete_refresh_token(refresh_token_record.id)
        tokens: AuthTokensSchema = await self.auth_service.generate_tokens(
            user
        )

        return RefreshTokenResponseSchema(data=tokens)

    async def get_socketio_token(self, environ: dict) -> str:
        return await self.auth_service.get_socketio_token(environ)

    async def handle_oauth_user(self, user_info: dict) -> SignUpResponseSchema:
        email = user_info.get("email")
        name = user_info.get("name")
        if "." in name:
            name = name.replace(".", "")
        avatar = user_info.get("picture")

        user = await self.user_service.get_user_by_email(email)
        if not user:
            user = await self.user_service.create_user_oauth(
                name=name,
                email=email,
                avatar=avatar,
            )

        tokens = await self.auth_service.generate_tokens(user)
        return SignUpResponseSchema(data=tokens)

    async def exchange_code_for_token(self, config: dict, code: str) -> dict:
        """Обмен authorization_code на access_token."""
        data = {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": env.oauth_redirect_uri,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(config["token_url"], data=data)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400, detail="Failed to exchange code for token"
                )
            token_data = response.json()
            if "error" in token_data:
                raise HTTPException(
                    status_code=400,
                    detail=token_data.get("error_description", "Token exchange error"),
                )
            return token_data

    async def get_google_user_info(self, access_token: str) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo", headers=headers
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400, detail="Failed to fetch Google user info"
                )
            user_data = response.json()
        return {
            "email": user_data["email"],
            "name": user_data.get("name"),
            "picture": user_data.get("picture"),
        }

    async def get_yandex_user_info(self, access_token: str) -> dict:
        params = {
            "access_token": access_token, 
            "format": "json"
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://login.yandex.ru/info", 
                params=params
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400, detail="Failed to fetch Yandex user info"
                )
            user_data = response.json()
        return {
            "email": user_data.get("default_email"),
            "name": user_data.get("real_name") or user_data.get("display_name"),
            "picture": user_data.get("default_avatar_id") and f"https://avatars.yandex.net/get-yapic/{user_data.get('default_avatar_id')}/islands-200",
        }
