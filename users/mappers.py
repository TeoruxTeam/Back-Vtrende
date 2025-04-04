from typing import List

from admin.schemas import AdminPUserDataSchema

from .models import User
from .schemas import UserDTO, UserWithPasswordDTO


class UserMapper:
    @staticmethod
    def to_dto(user: User) -> UserDTO:
        return UserDTO(
            id=user.id,
            name=user.name,
            surname=user.surname,
            email=user.email,
            phone_number=user.phone_number,
            avatar=user.avatar,
            is_admin=user.is_admin,
            is_active=user.is_active,
            is_activated=user.is_activated,
            is_banned=user.is_banned,
            is_deleted=user.is_deleted,
            created_at=user.created_at,
        )

    @staticmethod
    def to_dto_with_pwd(user: User) -> UserWithPasswordDTO:
        return UserWithPasswordDTO(
            id=user.id,
            name=user.name,
            surname=user.surname,
            email=user.email,
            phone_number=user.phone_number,
            avatar=user.avatar,
            is_admin=user.is_admin,
            is_active=user.is_active,
            is_activated=user.is_activated,
            is_banned=user.is_banned,
            is_deleted=user.is_deleted,
            created_at=user.created_at,
            password=user.password,
        )

    @staticmethod
    def to_adminp_user_data(user: User) -> AdminPUserDataSchema:
        return AdminPUserDataSchema(
            email=user.email,
            phone_number=user.phone_number,
            id=user.id,
            name=user.name,
            surname=user.surname,
            avatar=user.avatar,
            created_at=user.created_at,
            is_banned=user.is_banned,
            banned_at=user.banned_at,
            is_deleted=user.is_deleted,
            deleted_at=user.deleted_at,
            is_active=user.is_active,
            is_activated=user.is_activated,
        )

    @staticmethod
    def to_adminp_user_data_list(users: List[User]) -> List[AdminPUserDataSchema]:
        return [
            AdminPUserDataSchema(
                email=user.email,
                phone_number=user.phone_number,
                id=user.id,
                name=user.name,
                surname=user.surname,
                avatar=user.avatar,
                created_at=user.created_at,
                is_banned=user.is_banned,
                banned_at=user.banned_at,
                is_deleted=user.is_deleted,
                deleted_at=user.deleted_at,
                is_active=user.is_active,
                is_activated=user.is_activated,
            )
            for user in users
        ]
