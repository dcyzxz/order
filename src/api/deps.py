from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.exceptions import AuthError
from src.core.security import verify_token
from src.models.user import User


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get the current authenticated user from JWT token."""
    if not authorization.startswith("Bearer "):
        raise AuthError(message="Invalid authorization header")

    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    if payload is None:
        raise AuthError(message="Invalid or expired token")

    user_id = int(payload.get("sub", 0))
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if user is None:
        raise AuthError(message="User not found")

    return user


async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get the current admin user."""
    if current_user.role != "admin":
        raise AuthError(message="Admin access required", code=403)
    return current_user
