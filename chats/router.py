from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Request

from auth.depends import get_current_confirmed_user
from core.container import Container
from users.schemas import UserDTO

from .facade import IChatFacade
from .schemas import GetDetailChatResponseSchema, ReadChatResponseSchema

router = APIRouter(
    prefix="/listings/chats",
    tags=["listing_chats"],
)


@router.get("/{chat_id}", response_model=GetDetailChatResponseSchema)
@inject
async def get_detail_chat(
    request: Request,
    chat_id: int,
    limit: int = Query(20, description="Number of messages to return"),
    offset: int = Query(0, description="Number of messages to skip"),
    chat_facade: IChatFacade = Depends(Provide[Container.chat_facade]),
    user: UserDTO = Depends(get_current_confirmed_user),
):
    return await chat_facade.get_detail_chat(
        chat_id, user.id, request.base_url, limit, offset
    )


@router.patch("/{chat_id}/read", response_model=ReadChatResponseSchema)
@inject
async def read_chat(
    chat_id: int,
    chat_facade: IChatFacade = Depends(Provide[Container.chat_facade]),
    user: UserDTO = Depends(get_current_confirmed_user),
):
    return await chat_facade.read_chat(chat_id, user.id)
