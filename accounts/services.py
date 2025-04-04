import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from core.email_sender import EmailSender
from core.environment import env
from users.schemas import UserDTO
from users.services import UserService

from .exceptions import (
    InvalidRecoveryToken,
    InvalidVerificationToken,
    UserAlreadyActivated,
)
from .repositories import RecoveryTokenRepository, VerificationTokenRepository
from .schemas import (
    RecoveryTokenDTO,
    ResetPasswordRequestSchema,
    ResetPasswordResponseSchema,
    SendRecoveryTokenRequestSchema,
    SendRecoveryTokenResponseSchema,
    SendVerificationTokenResponseSchema,
    VerificationTokenDTO,
    VerifyUserRequestSchema,
    VerifyUserResponseSchema,
)


class VerificationTokenService:
    """Verification token service"""

    def __init__(self, repo: VerificationTokenRepository):
        self.repo = repo

    async def _generate_verification_token(self):
        verification_code = secrets.randbelow(1000000)
        return f"{verification_code:06d}"

    async def send_verification_token(
        self, user: UserDTO, email_sender: EmailSender
    ) -> None:

        await self.delete_verification_token_by_user(user)
        token = await self._generate_verification_token()

        expiration_time = datetime.now(timezone.utc) + timedelta(minutes=10)
        await self.repo.save_verification_token(user, token, expiration_time)
        await email_sender.send_email(
            user.email,
            "Verify your account",
            f"Your token for e-mail verification is: {token}",
        )

    async def delete_verification_token_by_user(self, user: UserDTO) -> None:
        await self.repo.delete_verification_token_by_user(user)

    async def verify_token(self, user: UserDTO, verification_token: str) -> bool:
        user_token: VerificationTokenDTO = (
            await self.repo.get_verification_token_by_user(user)
        )
        if user_token.token != verification_token:
            return False
        elif user_token.expiration < datetime.now(timezone.utc):
            return False
        return True


class RecoveryTokenService:
    """Recovery token service implementation"""

    def __init__(self, repo: RecoveryTokenRepository):
        self.repo = repo

    async def _generate_recovery_code(self, email: str):
        secret_key = env.secret_key
        random_data = secrets.token_hex(32)
        message = f"{email}{random_data}".encode("utf-8")
        token = hmac.new(
            secret_key.encode("utf-8"), message, hashlib.sha256
        ).hexdigest()
        return token

    async def send_recovery_token(
        self, user: UserDTO, email_sender: EmailSender
    ) -> None:
        await self.delete_recovery_token_by_user_id(user.id)
        recovery_code = await self._generate_recovery_code(user.email)

        expiration_time = datetime.now(timezone.utc) + timedelta(minutes=10)
        await self.repo.save_recovery_token(user, recovery_code, expiration_time)
        await email_sender.send_email(
            user.email,
            "Recovery code",
            f"{env.frontend_url}/reset-password?code={recovery_code}",
        )

    async def delete_recovery_token_by_user_id(self, user_id: int) -> None:
        await self.repo.delete_recovery_token_by_user_id(user_id)

    async def get_recovery_token_by_token(self, token: str) -> RecoveryTokenDTO:
        time_now = datetime.now(timezone.utc)
        return await self.repo.get_recovery_token_by_token(token, time_now)


class VerificationFacade:
    """Verification facade"""

    def __init__(
        self,
        user_service: UserService,
        verification_code_service: VerificationTokenService,
    ):
        self.user_service = user_service
        self.verification_code_service = verification_code_service

    async def send_verification_token(
        self,
        user: UserDTO,
        email_sender: EmailSender,
    ) -> SendVerificationTokenResponseSchema:
        if user.is_activated:
            raise UserAlreadyActivated()

        await self.verification_code_service.send_verification_token(user, email_sender)
        return SendVerificationTokenResponseSchema()

    async def verify_user(
        self, user: UserDTO, schema: VerifyUserRequestSchema
    ) -> VerifyUserResponseSchema:
        if not await self.verification_code_service.verify_token(user, schema.token):
            raise InvalidVerificationToken()
        await self.user_service.verify_user(user)
        await self.verification_code_service.delete_verification_token_by_user(user)
        return VerifyUserResponseSchema()


class RecoveryFacade:
    """Recovery facade"""

    def __init__(
        self,
        user_service: UserService,
        recovery_token_service: RecoveryTokenService,
    ):
        self.user_service = user_service
        self.recovery_token_service = recovery_token_service

    async def send_recovery_code(
        self,
        schema: SendRecoveryTokenRequestSchema,
        email_sender: EmailSender,
    ) -> SendRecoveryTokenResponseSchema:
        user = await self.user_service.get_user_by_email(schema.email)
        await self.recovery_token_service.send_recovery_token(user, email_sender)
        return SendRecoveryTokenResponseSchema()

    async def reset_password(
        self, schema: ResetPasswordRequestSchema
    ) -> ResetPasswordResponseSchema:
        token: RecoveryTokenDTO = (
            await self.recovery_token_service.get_recovery_token_by_token(schema.token)
        )
        if not token:
            raise InvalidRecoveryToken()

        new_password_hashed = await self.user_service.get_password_hash(
            schema.new_password
        )

        await self.user_service.update_password_by_user_id(
            token.user_id, new_password_hashed
        )
        await self.recovery_token_service.delete_recovery_token_by_user_id(
            token.user_id
        )
        return ResetPasswordResponseSchema()
