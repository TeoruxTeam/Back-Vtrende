from fastapi import HTTPException


class UserAlreadyExists(HTTPException):
    def __init__(self, message: str = None):
        super().__init__(status_code=400, detail="error.auth.user.exists")


class InvalidCredentials(HTTPException):
    def __init__(self, message: str = None):
        super().__init__(status_code=400, detail="error.auth.invalid.credentials")

class MissingToken(HTTPException):
    def __init__(self, message: str = None):
        super().__init__(status_code=400, detail="error.auth.token.missing")

class InvalidToken(HTTPException):
    def __init__(self, message: str = None):
        super().__init__(status_code=400, detail="error.auth.token.invalid")

class InvalidTokenFormat(HTTPException):
    def __init__(self, message: str = None):
        super().__init__(status_code=400, detail="error.auth.token.format.invalid")