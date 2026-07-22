from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    """Unified API response format."""

    code: int = 200
    message: str = "Success"
    data: T | None = None


class PaginationParams(BaseModel):
    """Pagination query parameters."""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")


class PaginatedData(BaseModel, Generic[T]):
    """Paginated data wrapper."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginatedResponse(Response[PaginatedData[T]], Generic[T]):
    """Paginated API response."""

    pass
