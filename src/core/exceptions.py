from __future__ import annotations

from typing import Any


class OrderException(Exception):
    """Base business exception for the ordering system."""

    def __init__(self, code: int = 400, message: str = "Request failed", data: Any = None) -> None:
        self.code = code
        self.message = message
        self.data = data
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "data": self.data}


class NotFoundError(OrderException):
    """Resource not found (404)."""

    def __init__(self, message: str = "Resource not found", data: Any = None) -> None:
        super().__init__(code=404, message=message, data=data)


class BusinessError(OrderException):
    """Business logic error (400)."""

    def __init__(self, message: str = "Business error", data: Any = None) -> None:
        super().__init__(code=400, message=message, data=data)


class AuthError(OrderException):
    """Authentication / authorization error (401/403)."""

    def __init__(self, message: str = "Authentication failed", code: int = 401, data: Any = None) -> None:
        super().__init__(code=code, message=message, data=data)
