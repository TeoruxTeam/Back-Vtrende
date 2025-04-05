from datetime import datetime

from fastapi import HTTPException
from pydantic import BaseModel, EmailStr, field_validator, model_validator

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
    email: EmailStr
    password: str
    is_shop: bool
    iin_bin: str | None = None

    @field_validator("email")
    def email_to_lowercase(cls, value):
        """Преобразует email в нижний регистр"""
        return value.lower() if value else value

    @field_validator("password")
    def validate_password_complexity(cls, value):
        """
        Проверяет, что пароль:
        - Содержит минимум 8 символов
        """
        if len(value) < 8:
            raise HTTPException(detail="error.password.must_contain.at_least_8_characters", status_code=400)
        return value

    @field_validator("iin_bin")
    def iin_bin_validator(cls, value, info):
        """Проверяет корректность ИИН/БИН"""
        if value is None:
            return value
        
        if len(value) != 12:
            raise HTTPException(detail="error.iin_bin.must_contain.12_digits", status_code=400)
            
        if not value.isdigit():
            raise HTTPException(detail="error.iin_bin.must_contain.only_digits", status_code=400)
            
        weights_1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        weights_2 = [3, 4, 5, 6, 7, 8, 9, 10, 11, 1, 2]
        
        # Первая проверка
        sum_1 = sum(int(value[i]) * weights_1[i] for i in range(11))
        control_digit_1 = sum_1 % 11
        
        # Если контрольная цифра равна 10, применяем вторую проверку
        if control_digit_1 == 10:
            sum_2 = sum(int(value[i]) * weights_2[i] for i in range(11))
            control_digit_1 = sum_2 % 11
            
        # Проверка совпадения контрольной цифры
        if control_digit_1 != int(value[11]):
            raise HTTPException(detail="error.iin_bin.invalid_control_sum", status_code=400)
            
        return value
    
    @model_validator(mode='after')
    def validate_shop_requirements(self):
        """Проверяет, что если пользователь является магазином, то указан ИИН/БИН"""
        if self.is_shop and not self.iin_bin:
            raise HTTPException(detail="error.iin_bin.required_for_shop", status_code=400)
        return self

class SignInSchema(BaseModel):
    email: EmailStr
    password: str
    
    @field_validator("email")
    def email_to_lowercase(cls, value):
        """Преобразует email в нижний регистр"""
        return value.lower() if value else value

class AccessTokenSchema(BaseModel):
    exp: str
    id: int
    email: EmailStr
    name: str
    verified: bool


class RefreshTokenRequestSchema(BaseModel):
    refresh_token: str


class RefreshTokenDTO(BaseModel):
    id: int
    refresh_token: str
    expiration: datetime
    user_id: int


class OAuthCodeSchema(BaseModel):
    code: str
