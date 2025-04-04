from fastapi import HTTPException


class InvalidVerificationToken(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="error.verification.code.invalid")


class UserAlreadyActivated(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=400, detail="error.verification.user.already_activated"
        )


class InvalidRecoveryToken(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="error.recovery.code.invalid")


class HostingIsBlockingSMTP(HTTPException):
    def __init__(self, code: int):
        super().__init__(status_code=418, detail=f"code {code}")
