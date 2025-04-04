from abc import ABC, abstractmethod
from datetime import datetime, timezone

from fastapi import HTTPException
from yookassa import Payment
from yookassa.domain.common import SecurityHelper

from core.logger import logger
from listings.services import IListingService
from promotions.schemas import PromotionOrderDTO
from promotions.services import IPromotionService
from users.schemas import UserDTO

from .schemas import (
    CreatePaymentLinkRequest,
    CreatePaymentLinkResponse,
    GetPaymentsResponse,
    PaymentUrlSchema,
    WebhookRequest,
)
from .services import IPaymentService


class IPaymentFacade(ABC):

    @abstractmethod
    async def get_payments(
        self, user_id: int, limit: int, offset: int
    ) -> GetPaymentsResponse:
        pass

    @abstractmethod
    async def create_payment(
        self,
        payment_request: CreatePaymentLinkRequest,
        current_user: UserDTO,
        language: str,
    ) -> CreatePaymentLinkResponse:
        pass

    @abstractmethod
    async def handle_webhook(self, payload: dict, ip_address: str):
        pass


class PaymentFacade(IPaymentFacade):

    def __init__(
        self,
        payment_service: IPaymentService,
        promotion_service: IPromotionService,
        listing_service: IListingService,
    ):
        self._payment_service = payment_service
        self._promotion_service = promotion_service
        self._listing_service = listing_service

    async def get_payments(
        self, user_id: int, limit: int, offset: int
    ) -> GetPaymentsResponse:
        payments, count = await self._promotion_service.get_orders(
            user_id, limit, offset
        )
        return GetPaymentsResponse(data=payments, count=count)

    async def create_payment(
        self,
        payment_request: CreatePaymentLinkRequest,
        current_user: UserDTO,
        language: str,
    ) -> CreatePaymentLinkResponse:
        tariff = await self._promotion_service.get_tariff(
            payment_request.tariff_id, language
        )
        if not tariff:
            raise HTTPException(
                status_code=404, detail="error.promotion_tariff.not_found"
            )

        listing = await self._listing_service.get_approved_listing_by_id(
            payment_request.listing_id
        )
        if not listing or listing.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="error.listing.not_found")

        order_id = await self._promotion_service.add_order(listing.id, tariff.id)

        payment_url = await self._payment_service.create_payment(
            tariff.price, order_id, tariff.description
        )

        return CreatePaymentLinkResponse(data=PaymentUrlSchema(url=payment_url))

    async def capture_payment(self, payment_id: str, amount: str):
        logger.info(f"Capturing payment {payment_id} with amount {amount}")
        try:
            response = Payment.capture(
                payment_id, {"amount": {"value": amount, "currency": "RUB"}}
            )
            logger.info(f"Payment {payment_id} captured successfully: {response}")
            return response
        except Exception as e:
            logger.error(f"Error capturing payment {payment_id}: {e}")
            raise

    async def handle_webhook(self, payload: dict, ip_address: str):

        if not SecurityHelper().is_ip_trusted(ip_address):
            logger.info(f"Payment webhook received from untrusted IP {ip_address}")
            return HTTPException(status_code=400, detail="error.webhook.untrusted_ip")

        metadata = payload.get("object", {}).get("metadata", {})
        order_id = int(metadata.get("order_id"))

        order = await self._promotion_service.get_order(order_id)
        if not order:
            raise HTTPException(
                status_code=404, detail="error.promotion_order.not_found"
            )

        status = payload.get("object", {}).get("status")
        if status == "waiting_for_capture":
            logger.info("Processing payment.waiting_for_capture")
            # Подтверждение платежа через ЮKassa SDK
            payment_id = payload.get("object", {}).get("id")
            amount = payload.get("object", {}).get("amount", {}).get("value")

            try:
                await self.capture_payment(payment_id, amount)
                start_date = datetime.now(timezone.utc)
                end_date = await self._promotion_service.calculate_end_date(
                    order.tariff_id
                )
                await self._promotion_service.confirm_order(
                    order_id, start_date, end_date
                )
                logger.info(f"Order {order_id} confirmed and payment captured.")
            except Exception as e:
                logger.error(f"Error capturing payment: {e}")
                raise HTTPException(
                    status_code=500, detail="error.payment.capture_failed"
                )
        elif status == "succeeded":
            logger.info("Payment succeeded, confirming order.")
            start_date = datetime.now(timezone.utc)
            end_date = await self._promotion_service.calculate_end_date(order.tariff_id)
            await self._promotion_service.confirm_order(order_id, start_date, end_date)
        elif status == "canceled":
            logger.info("Payment canceled, cancelling order.")
            await self._promotion_service.cancel_order(order_id)
        else:
            logger.error(f"Unhandled payment status: {status}")
            raise HTTPException(status_code=400, detail="error.webhook.unknown_status")
