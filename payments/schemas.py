from pydantic import BaseModel

from core.schemas import CountSchema, StatusOkSchema


class PaymentSchema(BaseModel):
    id: int
    amount: float
    status: str
    created_at: str
    updated_at: str


class GetPaymentsResponse(StatusOkSchema, CountSchema):
    payments: list[PaymentSchema]


class PaymentUrlSchema(BaseModel):
    url: str


class CreatePaymentLinkRequest(BaseModel):
    listing_id: int
    tariff_id: int


class WebhookMetadata(BaseModel):
    order_id: int


class WebhookRequest(BaseModel):
    status: str
    metadata: WebhookMetadata


class CreatePaymentLinkResponse(StatusOkSchema):
    data: PaymentUrlSchema
    message: str = "success.payment.created"
