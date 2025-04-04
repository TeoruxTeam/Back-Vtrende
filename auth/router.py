from authlib.integrations.base_client.errors import MismatchingStateError
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Request

from core.container import Container
from core.environment import env

from .facade import AuthFacade
from .schemas import (
    OAuthCodeSchema,
    RefreshTokenRequestSchema,
    RefreshTokenResponseSchema,
    SignInSchema,
    SignUpResponseSchema,
    SignUpSchema,
)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

        
@router.post("/google", response_model=SignUpResponseSchema)
@inject
async def auth_google(
    schema: OAuthCodeSchema,
    auth_facade: AuthFacade = Depends(Provide[Container.auth_facade]),
):
    config = {
        "client_id": env.google_client_id,
        "client_secret": env.google_secret,
        "token_url": "https://oauth2.googleapis.com/token",
    }
    token_response = await auth_facade.exchange_code_for_token(config, schema.code)
    access_token = token_response["access_token"]
    user_info = await auth_facade.get_google_user_info(access_token)
    user = await auth_facade.handle_oauth_user(user_info)
    return user


@router.post("/yandex", response_model=SignUpResponseSchema)
@inject
async def auth_yandex(
    schema: OAuthCodeSchema,
    auth_facade: AuthFacade = Depends(Provide[Container.auth_facade]),
):
    config = {
        "client_id": env.yandex_client_id,
        "client_secret": env.yandex_secret,
        "token_url": "https://oauth.yandex.com/token",
    }
    token_response = await auth_facade.exchange_code_for_token(config, schema.code)
    access_token = token_response["access_token"]
    user_info = await auth_facade.get_yandex_user_info(access_token)
    user = await auth_facade.handle_oauth_user(user_info)
    return user


@router.post("/sign-up/", response_model=SignUpResponseSchema)
@inject
async def sign_up(
    schema: SignUpSchema,
    auth_facade: AuthFacade = Depends(Provide[Container.auth_facade]),
):
    if "." in schema.name:
        raise HTTPException(status_code=400, detail="error.user.name_has_dots")
    return await auth_facade.sign_up(schema)


@router.post("/sign-in/", response_model=SignUpResponseSchema)
@inject
async def sign_in(
    schema: SignInSchema,
    auth_facade: AuthFacade = Depends(Provide[Container.auth_facade]),
):
    return await auth_facade.sign_in(schema)


@router.post("/refresh-token/", response_model=RefreshTokenResponseSchema)
@inject
async def refresh_token(
    schema: RefreshTokenRequestSchema,
    auth_facade: AuthFacade = Depends(Provide[Container.auth_facade]),
):
    return await auth_facade.refresh_token(schema)


@router.post("/sign-out/")
@inject
async def sign_out(
    schema: RefreshTokenRequestSchema,
    auth_facade: AuthFacade = Depends(Provide[Container.auth_facade]),
):
    return await auth_facade.sign_out(schema)
