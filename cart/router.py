from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide
from core.container import Container
from cart.services import CartService
from users.schemas import UserDTO
from auth.depends import get_current_verified_buyer
from cart.schemas import AddToCartResponseSchema, GetCartResponseSchema, CreateOrderResponseSchema
router = APIRouter(
    prefix="/cart",
    tags=["cart"]
)


@router.post("/add/{item_id}/")
@inject
async def add_to_cart(
    item_id: int,
    cart_service: CartService = Depends(Provide[Container.cart_service]),
    user: UserDTO = Depends(get_current_verified_buyer)
) -> AddToCartResponseSchema:
    """Add item to cart"""
    return await cart_service.add_to_cart(item_id, user.id)


@router.get("/")
@inject
async def get_cart(
    limit: int = 10,
    offset: int = 0,
    cart_service: CartService = Depends(Provide[Container.cart_service]),
    user: UserDTO = Depends(get_current_verified_buyer)
) -> GetCartResponseSchema:
    """Get cart"""
    return await cart_service.get_cart(user.id, limit, offset)


@router.delete("/decrease/{item_id}/")
@inject
async def decrease_from_cart(
    item_id: int,
    cart_service: CartService = Depends(Provide[Container.cart_service]),
    user: UserDTO = Depends(get_current_verified_buyer)
) -> None:
    """Decrease item quantity in cart -1"""
    return await cart_service.decrease_item_quantity(item_id, user.id)


@router.delete("/remove/{item_id}/")
@inject
async def remove_from_cart(
    item_id: int,
    cart_service: CartService = Depends(Provide[Container.cart_service]),
    user: UserDTO = Depends(get_current_verified_buyer)
) -> None:
    """Remove item from cart"""
    return await cart_service.remove_from_cart(item_id, user.id)


