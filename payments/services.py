from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional

from yookassa import Payment

from .schemas import WebhookRequest


class IPaymentService(ABC):

    @abstractmethod
    async def create_payment(
        self, tariff_price: Decimal, order_id: int, description: Optional[str] = None
    ) -> str:
        pass


class PaymentService(IPaymentService):

    async def create_payment(
        self, tariff_price: Decimal, order_id: int, description: Optional[str] = None
    ) -> str:
        payment = Payment.create(
            {
                "amount": {"value": tariff_price, "currency": "RUB"},
                "capture_mode": "AUTOMATIC",
                "confirmation": {
                    "type": "redirect",
                    "return_url": "https://vivli.ge/payments/redirect",
                },
                "description": description if description else "Vivli promotion",
                "metadata": {"order_id": order_id},
            }
        )
        return payment.confirmation.confirmation_url
