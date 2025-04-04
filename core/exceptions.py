from typing import Any, Optional

from fastapi import HTTPException, status


class AuthError(HTTPException):
    def __init__(
        self, detail: Any = None, headers: Optional[dict[str, Any]] = None
    ) -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail, headers)


class PermissionDeniedError(HTTPException):
    def __init__(
        self, detail: Any = None, headers: Optional[dict[str, Any]] = None
    ) -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, detail, headers)


class NotFoundError(HTTPException):
    def __init__(
        self, detail: Any = None, headers: Optional[dict[str, Any]] = None
    ) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, detail, headers)


class ValidationError(HTTPException):
    def __init__(
        self, detail: Any = None, headers: Optional[dict[str, Any]] = None
    ) -> None:
        super().__init__(status.HTTP_400_BAD_REQUEST, detail, headers)
