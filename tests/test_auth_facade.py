from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from auth.exceptions import InvalidCredentials, UserAlreadyExists
from auth.facade import AuthFacade
from auth.schemas import SignInSchema, SignUpSchema
from users.schemas import UserDTO


@pytest.mark.asyncio
async def test_sign_up_existing_user():
    # Arrange
    user_service_mock = AsyncMock()
    auth_service_mock = AsyncMock()
    facade = AuthFacade(user_service=user_service_mock, auth_service=auth_service_mock)
    schema = SignUpSchema(
        name="John", email="shogo.ryaskov@gmail.com", password="password"
    )
    user_service_mock.get_user_by_email.return_value = UserDTO(
        id=1,
        email="shogo.ryaskov@gmail.com",
        name="John",
        surname="Cena",
        is_admin=False,
        is_active=True,
        is_activated=True,
        created_at=datetime.now(timezone.utc),
        password="1234qwer",
    )

    # Act & Assert
    with pytest.raises(UserAlreadyExists):
        await facade.sign_up(schema)


@pytest.mark.asyncio
async def test_sign_in_invalid_credentials():
    # Arrange
    user_service_mock = AsyncMock()
    auth_service_mock = AsyncMock()
    facade = AuthFacade(user_service=user_service_mock, auth_service=auth_service_mock)
    schema = SignInSchema(
        email="shogo.ryaskov@gmail.com", password="wrong_password", remember_me=False
    )
    user_service_mock.get_user_by_email.return_value = None

    # Act & Assert
    with pytest.raises(InvalidCredentials):
        await facade.sign_in(schema)
