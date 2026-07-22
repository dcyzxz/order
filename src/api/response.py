from __future__ import annotations

import json
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Generic, TypeVar

from fastapi.responses import JSONResponse

from src.core.exceptions import OrderException
from src.schemas.common import Response, PaginatedData

T = TypeVar("T")


def _prepare(content: Any) -> Any:
    """Recursively convert non-JSON-serializable types to JSON-safe values."""
    if content is None:
        return None
    if isinstance(content, Decimal):
        return float(content)
    if isinstance(content, datetime):
        return content.isoformat()
    if isinstance(content, date):
        return content.isoformat()
    if isinstance(content, dict):
        return {k: _prepare(v) for k, v in content.items()}
    if isinstance(content, (list, tuple)):
        return [_prepare(i) for i in content]
    if isinstance(content, set):
        return [_prepare(i) for i in content]
    return content


def success(data: T | None = None, message: str = "Success") -> JSONResponse:
    """Return a success response."""
    body = Response(code=200, message=message, data=data)
    return JSONResponse(status_code=200, content=_prepare(body.model_dump(mode="python")))


def created(data: T | None = None, message: str = "Created") -> JSONResponse:
    """Return a 201 created response."""
    body = Response(code=201, message=message, data=data)
    return JSONResponse(status_code=201, content=_prepare(body.model_dump(mode="python")))


def paginated(
    items: list[T],
    total: int,
    page: int,
    page_size: int,
    message: str = "Success",
) -> JSONResponse:
    """Return a paginated response."""
    total_pages = max(1, (total + page_size - 1) // page_size)
    data = PaginatedData(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
    body = Response(code=200, message=message, data=data)
    return JSONResponse(status_code=200, content=_prepare(body.model_dump(mode="python")))


def error(code: int = 400, message: str = "Error", data: Any = None) -> JSONResponse:
    """Return an error response."""
    body = Response(code=code, message=message, data=data)
    return JSONResponse(status_code=code, content=_prepare(body.model_dump(mode="python")))


def handle_order_exception(exc: OrderException) -> JSONResponse:
    """Convert an OrderException to a JSON response."""
    return error(code=exc.code, message=exc.message, data=exc.data)
