from fastapi import HTTPException


class InvalidPassword(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="error.password.invalid")


class UserNotFound(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, detail="error.user.not_found")
