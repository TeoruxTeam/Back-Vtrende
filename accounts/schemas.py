from datetime import datetime

from pydantic import BaseModel, ConfigDict

from core.schemas import StatusOkSchema


class SendVerificationTokenResponseSchema(StatusOkSchema):
    message: str = "success.verification.token.sent"


class VerifyUserResponseSchema(StatusOkSchema):
    message: str = "success.verification.user.verified"


class SendRecoveryTokenResponseSchema(StatusOkSchema):
    message: str = "success.recovery.code.sent"


class ResetPasswordResponseSchema(StatusOkSchema):
    message: str = "success.password.reset"


class VerifyUserRequestSchema(BaseModel):
    token: str


class VerificationTokenDTO(BaseModel):
    id: int
    token: str
    user_id: int
    expiration: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SendRecoveryTokenRequestSchema(BaseModel):
    email: str


class ResetPasswordRequestSchema(BaseModel):
    token: str
    new_password: str


class RecoveryTokenDTO(BaseModel):
    id: int
    token: str
    user_id: int
    expiration: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)