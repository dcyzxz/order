from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.core.exceptions import OrderException
from src.core.logger import get_logger

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers for the FastAPI app."""

    @app.exception_handler(OrderException)
    async def order_exception_handler(request: Request, exc: OrderException) -> JSONResponse:
        logger.warning(
            "Business exception: code=%d message=%s path=%s",
            exc.code,
            exc.message,
            str(request.url),
        )
        return JSONResponse(
            status_code=exc.code,
            content={"code": exc.code, "message": exc.message, "data": exc.data},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Unhandled exception",
            extra={"path": str(request.url), "error": str(exc)},
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "Internal server error", "data": None},
        )
