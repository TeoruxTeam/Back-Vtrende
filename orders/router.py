from fastapi import APIRouter, Depends
from dependency_injector.annotations import inject, Provide
from core.container import Container
from orders.services import OrderService
from users.schemas import UserDTO
from orders.schemas import GetSelfOrdersResponseSchema
from auth.depends import get_current_verified_user, get_current_verified_seller_with_iin_bin

router = APIRouter(
    prefix="/orders",
    tags=["orders"]
)


@router.get("/self/")
@inject
async def get_self_orders(
    order_service: OrderService = Depends(Provide[Container.order_service]),
    user: UserDTO = Depends(get_current_verified_seller_with_iin_bin)
) -> GetSelfOrdersResponseSchema:
    """Get all orders as a shop"""
    return await order_service.get_self_orders(user)