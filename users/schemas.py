from datetime import datetime
from typing import Optional

import phonenumbers
from fastapi import Form, HTTPException
from pydantic import BaseModel, Field, field_validator

from core.schemas import StatusOkSchema


class UserPublicData(BaseModel):
    id: int
    name: Optional[str] = None
    surname: Optional[str] = None
    avatar: Optional[str] = None
    created_at: datetime
    phone_number: Optional[str] = None


class UserFlags(BaseModel):
    is_admin: bool
    is_active: bool
    is_activated: bool
    is_banned: bool
    is_deleted: bool


class UserContacts(BaseModel):
    email: Optional[str] = None


class UserDTO(UserPublicData, UserFlags, UserContacts):
    class Config:
        from_attributes = True


class UserWithPasswordDTO(UserDTO):
    password: str


class GetMeResponseSchema(StatusOkSchema):
    data: UserDTO


class PutMeRequestSchema(BaseModel):
    name: Optional[str] = Field(..., description="User name")
    surname: Optional[str] = Field(..., description="User surname")
    email: Optional[str] = Field(..., description="User email")
    phone_number: Optional[str] = Field(..., description="User phone number")
    delete_photo: Optional[bool] = Field(False, description="Delete user photo")

    @field_validator("phone_number")
    def validate_phone_number(cls, value: str) -> str:
        try:
            parsed_number = phonenumbers.parse(value, None)
            if not phonenumbers.is_valid_number(parsed_number):
                raise HTTPException(
                    status_code=422, detail="error.input.phone_number.invalid"
                )
            return phonenumbers.format_number(
                parsed_number, phonenumbers.PhoneNumberFormat.E164
            )
        except phonenumbers.NumberParseException:
            raise HTTPException(
                status_code=422, detail="error.input.phone_number.invalid"
            )

    @classmethod
    def as_form(
        cls,
        name: Optional[str] = Form(...),
        surname: Optional[str] = Form(None),
        email: Optional[str] = Form(...),
        phone_number: Optional[str] = Form(
            ..., description="About the format: Must start with +"
        ),
        delete_photo: Optional[bool] = Form(False),
    ):
        return cls(
            name=name,
            surname=surname,
            email=email,
            phone_number=phone_number,
            delete_photo=delete_photo,
        )


class PutMeResponseSchema(StatusOkSchema):
    message: str = "success.user.updated"
    data: UserDTO


class PatchPasswordResponseSchema(StatusOkSchema):
    message: str = "success.password.updated"


class PatchPasswordRequestSchema(BaseModel):
    old_password: str = Field(..., description="Old password")
    new_password: str = Field(..., description="New password")


class SellerInfo(BaseModel):
    id: int
    username: str
    rating: float = Field(..., ge=0, le=5)
    reviews_count: int
    avatar: Optional[str]
    phone_number: Optional[str]


class GetSellerInfoResponseSchema(BaseModel):
    data: SellerInfo
