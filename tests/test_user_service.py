from datetime import datetime, timezone
from unittest.mock import AsyncMock

import bcrypt
import pytest

from auth.schemas import SignUpSchema
from core.environment import env
from users.schemas import UserDTO
from users.services import UserService


@pytest.mark.asyncio
async def test_create_user():
    # Arrange
    repo_mock = AsyncMock()
    user_service = UserService(repo=repo_mock)
    schema = SignUpSchema(
        email="shogo.ryaskov@gmail.com",
        name="John",
        password="1234qwer",
    )
    hashed_password = "hashed_password"
    repo_mock.create_user.return_value = UserDTO(
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

    # Act
    user = await user_service.create_user(schema, hashed_password)

    # Assert
    assert user.id == 1
    assert user.email == schema.email


@pytest.mark.asyncio
async def test_verify_password():
    # Arrange
    repo_mock = AsyncMock()
    user_service = UserService(repo=repo_mock)
    password = "password"
    hashed_password = bcrypt.hashpw(
        (password + env.secret_key).encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    # Act
    is_valid = await user_service.verify_password(password, hashed_password)

    # Assert
    assert is_valid is True
