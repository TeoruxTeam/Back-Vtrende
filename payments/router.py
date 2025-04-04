from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Request

from auth.depends import get_current_confirmed_user
from core.container import Container
from core.logger import logger
from core.utils import get_language_from_cookies
from users.schemas import UserDTO

from .facade import IPaymentFacade
from .schemas import (
    CreatePaymentLinkRequest,
    CreatePaymentLinkResponse,
    GetPaymentsResponse,
    WebhookRequest,
)

router = APIRouter(
    prefix="/payments",
    tags=["payments"],
)


@router.get("/")
@inject
async def get_payments(
    limit: int = Query(10, ge=1, le=100, description="The number of items to return"),
    offset: int = Query(0, ge=0, description="The number of items to skip"),
    current_user: UserDTO = Depends(get_current_confirmed_user),
    payment_facade: IPaymentFacade = Depends(Provide[Container.payment_facade]),
) -> GetPaymentsResponse:
    return await payment_facade.get_payments(current_user.id, limit, offset)


@router.post("/create_payment_link/")
@inject
async def create_payment_link(
    payment_request: CreatePaymentLinkRequest,
    language: str = Depends(get_language_from_cookies),
    current_user: UserDTO = Depends(get_current_confirmed_user),
    payment_facade: IPaymentFacade = Depends(Provide[Container.payment_facade]),
) -> CreatePaymentLinkResponse:
    return await payment_facade.create_payment(payment_request, current_user, language)


@router.post("/webhook/")
@inject
async def payment_webhook(
    request: Request,
    payment_facade: IPaymentFacade = Depends(Provide[Container.payment_facade]),
):
    ip_address = request.headers.get("X-Real-IP") or request.client.host
    logger.info(f"Payment webhook received from {ip_address}")

    # Log the full request headers and body
    logger.info(f"Request headers: {dict(request.headers)}")
    try:
        payload = await request.json()
        logger.info(f"Request payload: {payload}")
    except Exception as e:
        logger.error(f"Failed to parse request payload: {e}")
        return {"status": "error", "message": "Invalid payload"}

    # Process the webhook using the payment facade
    try:
        await payment_facade.handle_webhook(payload, ip_address)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return {"status": "error", "message": "Internal server error"}
