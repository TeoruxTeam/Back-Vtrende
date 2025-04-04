from datetime import datetime

from pydantic import BaseModel, EmailStr

from core.schemas import StatusOkSchema


class AuthTokensSchema(BaseModel):
    access_expiration: datetime
    refresh_expiration: datetime
    access_token: str
    refresh_token: str


class SignUpResponseSchema(StatusOkSchema):
    message: str = "success.auth.signup"
    data: AuthTokensSchema


class RefreshTokenResponseSchema(StatusOkSchema):
    message: str = "success.auth.refresh_token"
    data: AuthTokensSchema


class SignInResponseSchema(StatusOkSchema):
    message: str = "success.auth.signin"
    data: AuthTokensSchema


class SignUpSchema(BaseModel):
    name: str
    email: EmailStr
    password: str


class SignInSchema(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool


class AccessTokenSchema(BaseModel):
    exp: str
    id: int
    email: EmailStr
    name: str
    is_activated: bool
    is_admin: bool


class RefreshTokenRequestSchema(BaseModel):
    refresh_token: str


class RefreshTokenDTO(BaseModel):
    id: int
    refresh_token: str
    expiration: datetime
    user_id: int


class OAuthCodeSchema(BaseModel):
    code: str
