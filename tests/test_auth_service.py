from datetime import datetime, timezone
from unittest.mock import AsyncMock

import jwt
import pytest

from auth.schemas import AuthTokensSchema
from auth.services import AuthService
from core.environment import env
from users.schemas import UserDTO


@pytest.mark.asyncio
async def test_create_access_token():
    # Arrange
    repo_mock = AsyncMock()
    auth_service = AuthService(repo=repo_mock)
    user = UserDTO(
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
    access_token, exp = await auth_service._create_access_token(user)

    # Assert
    assert isinstance(access_token, str)
    assert exp > datetime.now(timezone.utc)
    decoded_token = jwt.decode(
        access_token, env.secret_key, algorithms=[env.jwt_algorithm]
    )
    assert decoded_token["id"] == user.id
    assert decoded_token["email"] == user.email


@pytest.mark.asyncio
async def test_generate_tokens():
    # Arrange
    repo_mock = AsyncMock()
    auth_service = AuthService(repo=repo_mock)
    user = UserDTO(
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
    remember_me = False

    # Act
    tokens: AuthTokensSchema = await auth_service.generate_tokens(user, remember_me)

    # Assert
    assert isinstance(tokens, AuthTokensSchema)
    assert isinstance(tokens.access_token, str)
    assert isinstance(tokens.refresh_token, str)
    token_payload = jwt.decode(
        tokens.access_token, env.secret_key, algorithms=[env.jwt_algorithm]
    )

    assert token_payload["name"] == user.name
    assert token_payload["is_admin"] == user.is_admin
    assert token_payload["is_activated"] == user.is_activated
    assert token_payload["email"] == user.email
    assert token_payload["id"] == user.id
