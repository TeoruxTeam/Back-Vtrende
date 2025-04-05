from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from accounts.schemas import (
    ResetPasswordRequestSchema,
    ResetPasswordResponseSchema,
    SendRecoveryTokenRequestSchema,
    SendRecoveryTokenResponseSchema,
    SendVerificationTokenResponseSchema,
    VerifyUserRequestSchema,
    VerifyUserResponseSchema,
)
from accounts.services import RecoveryFacade, VerificationFacade
from auth.depends import (
    get_current_user, 
    get_current_verified_buyer, 
    get_current_verified_seller
)
from core.container import Container
from core.email_sender import EmailSender
from users.schemas import UserDTO

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
)


@router.post("/send-verification-token/", response_model=VerifyUserResponseSchema)
@inject
async def send_verification_token(
    user: UserDTO = Depends(get_current_user),
    verification_facade: VerificationFacade = Depends(
        Provide[Container.verification_facade]
    ),
    email_sender: EmailSender = Depends(Provide[Container.email_sender]),
):
    return await verification_facade.send_verification_token(
        user, email_sender
    )


@router.post("/verify/", response_model=SendVerificationTokenResponseSchema)
@inject
async def verify_user(
    schema: VerifyUserRequestSchema,
    user: UserDTO = Depends(get_current_user),
    verification_facade: VerificationFacade = Depends(
        Provide[Container.verification_facade]
    ),
):
    return await verification_facade.verify_user(user, schema)


@router.post("/send-recovery-code/", response_model=SendRecoveryTokenResponseSchema)
@inject
async def send_recovery_code(
    schema: SendRecoveryTokenRequestSchema,
    recovery_facade: RecoveryFacade = Depends(Provide[Container.recovery_facade]),
    email_sender: EmailSender = Depends(Provide[Container.email_sender]),
):
    return await recovery_facade.send_recovery_code(
        schema, email_sender
    )


@router.post("/reset-password/", response_model=ResetPasswordResponseSchema)
@inject
async def reset_password(
    schema: ResetPasswordRequestSchema,
    recovery_facade: RecoveryFacade = Depends(Provide[Container.recovery_facade]),
):
    return await recovery_facade.reset_password(schema)
