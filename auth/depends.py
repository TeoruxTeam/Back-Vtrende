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
async def get_current_seller(
    user_service: UserService = Depends(Provide[Container.user_service]),
    token: Optional[str] = Depends(JWTBearer()),
) -> UserWithPasswordDTO:
    if not token:
        raise AuthError(detail="error.auth.token_not_provided")
    payload = jwt.decode(token, env.secret_key, algorithms=[env.jwt_algorithm])
    logger.warning(f"getting current verified seller with pasyload: {payload}")
    current_user: UserWithPasswordDTO = await user_service.get_user_by_id(
        payload["id"], True
    )
    logger.warning(f"Current verified seller: {current_user}")

    if not current_user:
        raise AuthError(detail="error.auth.user.not_found")
    if not current_user.is_shop:
        raise AuthError(detail="error.auth.not_shop")
    logger.info(f"User {current_user.email} is verified seller")
    return current_user
    
@inject
async def get_current_verified_seller(
    user_service: UserService = Depends(Provide[Container.user_service]),
    token: Optional[str] = Depends(JWTBearer()),
) -> UserWithPasswordDTO:
    if not token:
        raise AuthError(detail="error.auth.token_not_provided")
    payload = jwt.decode(token, env.secret_key, algorithms=[env.jwt_algorithm])
    logger.warning(f"getting current verified seller with pasyload: {payload}")
    current_user: UserWithPasswordDTO = await user_service.get_user_by_id(
        payload["id"], True
    )
    logger.warning(f"Current verified seller: {current_user}")

    if not current_user:
        raise AuthError(detail="error.auth.user.not_found")
    if not current_user.verified:
        raise AuthError(detail="error.auth.user.not_verified")
    if not current_user.is_shop:
        raise AuthError(detail="error.auth.not_shop")
    logger.info(f"User {current_user.email} is verified seller")
    return current_user

@inject
async def get_current_verified_seller_with_iin_bin(
    user_service: UserService = Depends(Provide[Container.user_service]),
    token: Optional[str] = Depends(JWTBearer()),
) -> UserWithPasswordDTO:
    if not token:
        raise AuthError(detail="error.auth.token_not_provided")
    payload = jwt.decode(token, env.secret_key, algorithms=[env.jwt_algorithm])
    logger.warning(f"getting current verified seller with pasyload: {payload}")
    current_user: UserWithPasswordDTO = await user_service.get_user_by_id(
        payload["id"], True
    )
    logger.warning(f"Current verified seller: {current_user}")

    if not current_user:
        raise AuthError(detail="error.auth.user.not_found")
    elif not current_user.verified:
        raise AuthError(detail="error.auth.user.not_verified")
    elif not current_user.is_shop:
        raise AuthError(detail="error.auth.not_shop")
    elif not current_user.iin_bin:
        raise AuthError(detail="error.auth.iin_bin_not_provided")
    logger.info(f"User {current_user.email} is verified seller with iin_bin")
    return current_user

@inject
async def get_current_verified_buyer(
    user_service: UserService = Depends(Provide[Container.user_service]),
    token: Optional[str] = Depends(JWTBearer()),
) -> UserWithPasswordDTO:
    if not token:
        raise AuthError(detail="error.auth.token_not_provided")
    payload = jwt.decode(token, env.secret_key, algorithms=[env.jwt_algorithm])
    logger.warning(f"getting current verified buyer with pasyload: {payload}")
    current_user: UserWithPasswordDTO = await user_service.get_user_by_id(
        payload["id"], True
    )
    logger.warning(f"Current verified buyer: {current_user}")

    if not current_user:
        raise AuthError(detail="error.auth.user.not_found")
    if not current_user.verified:
        raise AuthError(detail="error.auth.user.not_verified")
    if current_user.is_shop:
        raise AuthError(detail="error.auth.is_shop")
    
    logger.info(f"User {current_user.email} is verified buyer")
    return current_user

@inject
async def get_current_verified_user(
    user_service: UserService = Depends(Provide[Container.user_service]),
    token: Optional[str] = Depends(JWTBearer()),
) -> UserWithPasswordDTO:
    if not token:
        raise AuthError(detail="error.auth.token_not_provided")
    payload = jwt.decode(token, env.secret_key, algorithms=[env.jwt_algorithm])
    logger.warning(f"getting current verified user with pasyload: {payload}")
    current_user: UserWithPasswordDTO = await user_service.get_user_by_id(
        payload["id"], True
    )
    logger.warning(f"Current verified user: {current_user}")

    if not current_user:
        raise AuthError(detail="error.auth.user.not_found")
    if not current_user.verified:
        raise AuthError(detail="error.auth.user.not_verified")
    
    logger.info(f"User {current_user.email} is verified user")
    return current_user