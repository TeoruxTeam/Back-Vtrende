from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, File, Query, Request, UploadFile

from auth.depends import get_current_confirmed_user, get_current_confirmed_user_optional
from users.schemas import UserDTO


router = APIRouter(
    prefix="/items",
    tags=["items"],
)
