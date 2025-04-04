from fastapi import HTTPException


class FCMTokenNotFound(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="error.fcm_token.not_found")
