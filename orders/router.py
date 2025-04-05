from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide
from core.container import Container
from orders.services import OrderService
from users.schemas import UserDTO
from orders.schemas import (
    GetSelfOrdersResponseSchema,
    CreateOrderResponseSchema,
    CreateBookingResponseSchema
)
from auth.depends import get_current_verified_buyer, get_current_verified_seller_with_iin_bin

router = APIRouter(
    prefix="/orders",
    tags=["orders"]
)


@router.post("/create/")
@inject
async def create_order(
    order_service: OrderService = Depends(Provide[Container.order_service]),
    user: UserDTO = Depends(get_current_verified_buyer)
) -> CreateOrderResponseSchema:
    """Create order"""
    return await order_service.create_order(user)


@router.get("/self/")
@inject
async def get_self_orders(
    order_service: OrderService = Depends(Provide[Container.order_service]),
    user: UserDTO = Depends(get_current_verified_seller_with_iin_bin)
) -> GetSelfOrdersResponseSchema:
    """Get all orders as a shop"""
    return await order_service.get_self_orders(user)



@router.post("/{item_id}/booking")
async def create_booking(
    item_id: int,
    order_service: OrderService = Depends(Provide[Container.order_service]),
    user: UserDTO = Depends(get_current_verified_buyer)
) -> CreateBookingResponseSchema:
    """Create booking"""
    return await order_service.create_booking(user)