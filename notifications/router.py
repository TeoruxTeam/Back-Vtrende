from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.depends import get_current_confirmed_user
from core.container import Container
from users.schemas import UserDTO

from .facade import INotificationFacade
from .models import FCMToken
from .schemas import (
    AddFCMTokenResponse,
    FCMTokenSchema,
    GetNotificationSettingsResponse,
    GetNotificationsResponse,
    PutNotificationSettingsRequest,
    PutNotificationSettingsResponse,
    ReadNotificationsRequest,
    ReadNotificationsResponse,
)

router = APIRouter(
    prefix="/notifications",
    tags=[
        "notifications",
    ],
)


@router.get("/", response_model=GetNotificationsResponse)
@inject
async def get_notifications(
    include_read: bool = Query(
        False, description="Bool to return notifications that already read"
    ),
    limit: int = Query(10, description="Notifications to return"),
    offset: int = Query(0, description="Notifications to skip"),
    notification_facade: INotificationFacade = Depends(
        Provide[Container.notification_facade]
    ),
    current_user: UserDTO = Depends(get_current_confirmed_user),
):
    return await notification_facade.get_notifications(
        current_user, limit, offset, include_read
    )


@router.patch("/read/", response_model=ReadNotificationsResponse)
@inject
async def read_notifications(
    payload: ReadNotificationsRequest,
    notification_facade: INotificationFacade = Depends(
        Provide[Container.notification_facade]
    ),
    current_user: UserDTO = Depends(get_current_confirmed_user),
):
    """Read notifications by ids"""
    return await notification_facade.read_notifications(payload, current_user)


@router.get("/settings/", response_model=GetNotificationSettingsResponse)
@inject
async def get_settings(
    notification_facade: INotificationFacade = Depends(
        Provide[Container.notification_facade]
    ),
    current_user: UserDTO = Depends(get_current_confirmed_user),
):
    return await notification_facade.get_notification_settings(current_user)


@router.put("/settings/", response_model=PutNotificationSettingsResponse)
@inject
async def update_settings(
    payload: PutNotificationSettingsRequest,
    notification_facade: INotificationFacade = Depends(
        Provide[Container.notification_facade]
    ),
    current_user: UserDTO = Depends(get_current_confirmed_user),
):
    return await notification_facade.update_notification_settings(payload, current_user)


@router.post("/fcm-tokens/add/", response_model=AddFCMTokenResponse)
@inject
async def add_token(
    token_data: FCMTokenSchema,
    notification_facade: INotificationFacade = Depends(
        Provide[Container.notification_facade]
    ),
    current_user: UserDTO = Depends(get_current_confirmed_user),
):
    return await notification_facade.add_fcm_token(token_data, current_user)


@router.delete("/fcm-tokens/{device_id:str}/")
@inject
async def delete_token(
    device_id: str,
    notification_facade: INotificationFacade = Depends(
        Provide[Container.notification_facade]
    ),
    current_user: UserDTO = Depends(get_current_confirmed_user),
):
    return await notification_facade.delete_fcm_token(device_id, current_user)
