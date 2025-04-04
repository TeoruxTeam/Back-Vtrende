from fastapi import HTTPException


class ChatNotFound(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, detail="error.chat.not_found")
