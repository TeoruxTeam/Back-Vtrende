from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager
from datetime import datetime
from typing import Any, Callable, Coroutine

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import delete

from core.repositories import BaseRepository
from users.schemas import UserDTO

from .models import RefreshToken
from .schemas import RefreshTokenDTO


class IRefreshTokenRepository(ABC):

    @abstractmethod
    async def save_refresh_token(
        self, user_id: int, refresh_token: str, expiration_datetime: datetime
    ) -> None:
        pass

    @abstractmethod
    async def get_refresh_token(self, refresh_token: str) -> RefreshTokenDTO:
        pass

    @abstractmethod
    async def delete_refresh_token_by_id(self, token_id: int) -> None:
        pass

    @abstractmethod
    async def delete_refresh_token_by_token(self, refresh_token: str) -> None:
        pass


class RefreshTokenRepository(IRefreshTokenRepository, BaseRepository):
    def __init__(
        self, session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]]
    ):
        self.session_factory = session_factory

    async def save_refresh_token(
        self, user_id: int, refresh_token: str, expiration_datetime: datetime
    ) -> None:
        async with self.session_factory() as session:
            refresh_token = RefreshToken(
                refresh_token=refresh_token,
                user_id=user_id,
                expiration=expiration_datetime,
            )
            session.add(refresh_token)
            await session.commit()

    async def get_refresh_token(self, refresh_token: str) -> RefreshTokenDTO:
        async with self.session_factory() as session:
            query = select(RefreshToken).filter(
                RefreshToken.refresh_token == refresh_token
            )
            results = await session.execute(query)
            token = results.scalars().first()
            if token:
                return RefreshTokenDTO(
                    id=token.id,
                    refresh_token=token.refresh_token,
                    expiration=token.expiration,
                    user_id=token.user_id,
                )
            return None

    async def delete_refresh_token_by_id(self, token_id: int) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                await session.execute(
                    delete(RefreshToken).where(RefreshToken.id == token_id)
                )

    async def delete_refresh_token_by_token(self, refresh_token: str) -> None:
        async with self.get_session() as session:
            async with session.begin():
                await session.execute(
                    delete(RefreshToken).where(
                        RefreshToken.refresh_token == refresh_token
                    )
                )
