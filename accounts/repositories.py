from datetime import datetime

from sqlalchemy import delete
from sqlalchemy.future import select

from core.repositories import BaseRepository
from users.schemas import UserDTO

from .models import RecoveryToken, VerificationToken
from .schemas import RecoveryTokenDTO, VerificationTokenDTO


class VerificationTokenRepository(BaseRepository):

    async def delete_verification_token_by_user(self, user: UserDTO) -> None:
        async with self.get_session() as session:
            stmt = delete(VerificationToken).where(VerificationToken.user_id == user.id)
            await session.execute(stmt)
            await session.commit()

    async def save_verification_token(
        self, user: UserDTO, token: str, expiration_time: datetime
    ) -> None:
        async with self.get_session() as session:
            verification_token = VerificationToken(
                user_id=user.id, token=token, expiration=expiration_time
            )
            session.add(verification_token)
            await session.commit()

    async def get_verification_token_by_user(
        self, user: UserDTO
    ) -> VerificationTokenDTO:
        async with self.get_session() as session:
            query = select(VerificationToken).where(
                VerificationToken.user_id == user.id
            )
            result = await session.execute(query)
            token: VerificationToken = result.scalars().first()
            if token:
                return VerificationTokenDTO.model_validate(token)
            return None


class RecoveryTokenRepository(BaseRepository):

    async def delete_recovery_token_by_user_id(self, user_id: int) -> None:
        async with self.get_session() as session:
            stmt = delete(RecoveryToken).where(RecoveryToken.user_id == user_id)
            await session.execute(stmt)
            await session.commit()

    async def save_recovery_token(
        self, user: UserDTO, token: str, expiration_time: datetime
    ) -> None:
        async with self.get_session() as session:
            recovery_token = RecoveryToken(
                user_id=user.id, token=token, expiration=expiration_time
            )
            session.add(recovery_token)
            await session.commit()

    async def get_recovery_token_by_token(
        self, token: str, time_now: datetime
    ) -> UserDTO:
        async with self.get_session() as session:
            query = select(RecoveryToken).where(
                RecoveryToken.token == token, RecoveryToken.expiration > time_now
            )
            result = await session.execute(query)
            token: RecoveryToken = result.scalars().first()
            if token:
                return RecoveryTokenDTO.model_validate(token)
            return None
