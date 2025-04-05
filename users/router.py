from typing import Optional

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, File, Request, UploadFile

from auth.depends import get_current_confirmed_user
from core.container import Container


from .schemas import (
    GetMeResponseSchema,
    PatchPasswordRequestSchema,
    PatchPasswordResponseSchema,
    PutMeRequestSchema,
    PutMeResponseSchema,
    UserDTO,
)
from .services import IUserService

router = APIRouter(
    prefix="/profile",
    tags=["profile"],
)


@router.get("/me/", response_model=GetMeResponseSchema)
@inject
async def get_me(
    request: Request,
    user_service: IUserService = Depends(Provide[Container.user_service]),
    user: UserDTO = Depends(get_current_confirmed_user),
):
    return await user_service.get_me(user, request.base_url)


@router.put("/me/", response_model=PutMeResponseSchema)
@inject
async def put_me(
    request: Request,
    payload: PutMeRequestSchema = Depends(PutMeRequestSchema.as_form),
    user_service: IUserService = Depends(Provide[Container.user_service]),
    photo: Optional[UploadFile] = File(
        None, description="User photo. If selected, it will replace the current one."
    ),
    user: UserDTO = Depends(get_current_confirmed_user),
):
    return await user_service.put_me(payload, photo, user, request.base_url)


@router.patch("/me/password/", response_model=PatchPasswordResponseSchema)
@inject
async def patch_password(
    payload: PatchPasswordRequestSchema,
    user_service: IUserService = Depends(Provide[Container.user_service]),
    user: UserDTO = Depends(get_current_confirmed_user),
):
    return await user_service.patch_password(payload, user)