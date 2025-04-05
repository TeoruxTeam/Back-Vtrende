from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import ValidationError

from auth.exceptions import InvalidTokenFormat, MissingToken
from core.environment import env
from core.exceptions import AuthError
from core.logger import logger
from users.schemas import UserDTO

from .repositories import RefreshTokenRepository
from .schemas import AccessTokenSchema, AuthTokensSchema, RefreshTokenDTO


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = False):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearer, self
        ).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise AuthError(detail="error.auth.scheme.invalid")
            if not self.verify_jwt(credentials.credentials):
                raise AuthError(detail="error.auth.token.invalid")
            return credentials.credentials
        else:
            return None

    @staticmethod
    def verify_jwt(jwt_token: str) -> bool:
        is_token_valid: bool = False
        try:
            payload = JWTBearer.decode_jwt(jwt_token)
            logger.warning(f"Payload: {payload}")
        except Exception as e:
            logger.warning(f"Error decoding JWT: {str(e)}")
            payload = None
        if payload:
            is_token_valid = True
        return is_token_valid

    @staticmethod
    def decode_jwt(token: str) -> dict:
        try:
            decoded_token = jwt.decode(
                token, env.secret_key, algorithms=[env.jwt_algorithm]
            )
            logger.warning(f"Decoded token: {decoded_token}")
            return (
                decoded_token
                if decoded_token["exp"]
                >= int(round(datetime.now(timezone.utc).timestamp()))
                else None
            )
        except Exception as e:
            logger.warning(f"Error decoding JWT: {str(e)}")
            return {}


class AuthService:
    def __init__(self, repo: RefreshTokenRepository):
        self.repo = repo

    async def _create_access_token(self, user: UserDTO) -> tuple[str, datetime]:
        expiration_datetime = datetime.now(timezone.utc) + timedelta(
            minutes=env.access_token_lifetime
        )

        payload = {
            "exp": expiration_datetime,
            "id": user.id,
            "email": user.email,
            "is_shop": user.is_shop,
            "verified": user.verified
        }
        access_token = jwt.encode(payload, env.secret_key, algorithm=env.jwt_algorithm)
        access_token_padded = self.add_padding_to_jwt(access_token)
        return access_token_padded, expiration_datetime

    async def _create_refresh_token(self, user: UserDTO) -> str:
        expiration_datetime = datetime.now(timezone.utc) + timedelta(
            minutes=env.refresh_token_lifetime
        )

        refresh_token_payload = {"user_id": user.id, "exp": expiration_datetime}
        refresh_token = jwt.encode(
            refresh_token_payload, env.secret_key, algorithm=env.jwt_algorithm
        )

        refresh_token_padded = self.add_padding_to_jwt(refresh_token)

        await self.repo.save_refresh_token(
            user.id, refresh_token_padded, expiration_datetime
        )
        return refresh_token_padded, expiration_datetime

    async def generate_tokens(
        self, user: UserDTO
    ) -> AuthTokensSchema:
        access_token, access_expiration = await self._create_access_token(user)
        refresh_token, refresh_expiration = await self._create_refresh_token(user)

        return AuthTokensSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            access_expiration=access_expiration,
            refresh_expiration=refresh_expiration,
        )

    def add_padding_to_jwt(self, token: str) -> str:
        """Добавляем паддинг для корректной длины токена"""
        token += "=" * (4 - len(token) % 4)
        return token

    async def verify_jwt(self, token: str) -> bool:
        try:
            payload = jwt.decode(token, env.secret_key, algorithms=[env.jwt_algorithm])
            token_data = AccessTokenSchema(**payload)
            return token_data
        except (jwt.PyJWTError, ValidationError) as e:
            logger.warning(f"Invalid JWT token, reason is {e}")
            raise AuthError(detail="error.auth.credentials.invalid")

    async def get_refresh_token(self, refresh_token: str) -> RefreshTokenDTO:
        return await self.repo.get_refresh_token(refresh_token)

    async def delete_refresh_token(self, refresh_token_id: int) -> None:
        await self.repo.delete_refresh_token_by_id(refresh_token_id)

    async def delete_refresh_token_by_token(self, refresh_token: str) -> None:
        await self.repo.delete_refresh_token_by_token(refresh_token)

    async def get_socketio_token(self, environ: dict) -> RefreshTokenDTO:
        headers = dict(environ["asgi.scope"].get("headers", []))
        auth_header = headers.get(b"authorization", None)

        if not auth_header:
            raise MissingToken()

        auth_header = auth_header.decode("utf-8")

        if not auth_header.startswith("Bearer "):
            raise InvalidTokenFormat()

        return auth_header.split("Bearer ")[1]
