from typing import Optional

import jwt
from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from core.container import Container
from core.environment import env
from core.exceptions import AuthError
from core.logger import logger
from users.schemas import UserWithPasswordDTO
from users.services import UserService

from .services import JWTBearer


@inject
async def get_current_user(
    user_service: UserService = Depends(Provide[Container.user_service]),
    token: Optional[str] = Depends(JWTBearer()),
) -> UserWithPasswordDTO:
    if not token:
        raise AuthError(detail="error.auth.token_not_provided")
    payload = jwt.decode(token, env.secret_key, algorithms=[env.jwt_algorithm])
    current_user: UserWithPasswordDTO = await user_service.get_user_by_id(
        payload["id"], True
    )
    if not current_user:
        raise AuthError(detail="error.auth.user.not_found")
    return current_user


@inject
async def get_current_confirmed_user(
    user_service: UserService = Depends(Provide[Container.user_service]),
    token: Optional[str] = Depends(JWTBearer()),
) -> UserWithPasswordDTO:
    if not token:
        raise AuthError(detail="error.auth.token_not_provided")
    payload = jwt.decode(token, env.secret_key, algorithms=[env.jwt_algorithm])
    logger.warning(f"getting current user with pasyload: {payload}")
    current_user: UserWithPasswordDTO = await user_service.get_user_by_id(
        payload["id"], True
    )
    logger.warning(f"Current user: {current_user}")
    if not current_user:
        raise AuthError(detail="error.auth.user.not_found")
    if not current_user.is_activated:
        raise AuthError(detail="error.auth.user.not_activated")
    if current_user.is_deleted:
        raise AuthError(detail="error.auth.user.not_found")
    if current_user.is_banned:
        raise AuthError(detail="error.auth.user.banned")
    logger.info(f"User {current_user.email} is activated")
    return current_user


@inject
async def get_current_confirmed_user_optional(
    user_service: UserService = Depends(Provide[Container.user_service]),
    token: Optional[str] = Depends(JWTBearer()),
) -> Optional[UserWithPasswordDTO]:
    if not token:
        logger.warning("Token is not provided")
        return None
    payload = jwt.decode(token, env.secret_key, algorithms=[env.jwt_algorithm])
    current_user: UserWithPasswordDTO = await user_service.get_user_by_id(
        payload["id"], True
    )
    if not current_user or not current_user.is_activated:
        return None
    return current_user
