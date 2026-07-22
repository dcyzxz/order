from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import AuthError
from src.core.security import create_access_token
from src.models.user import User


class UserService:
    """用户相关业务逻辑."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def login_by_wechat(self, code: str, nick_name: str | None = None, avatar_url: str | None = None) -> tuple[User, str]:
        """
        微信登录。
        生产环境应调用微信服务器验证 code，此处简化为 mock。
        """
        mock_openid = f"mock_openid_{code}"

        result = await self.db.execute(select(User).where(User.openid == mock_openid))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                openid=mock_openid,
                nickname=nick_name,
                avatar_url=avatar_url,
            )
            self.db.add(user)
            await self.db.flush()

        token = create_access_token(
            subject=str(user.id),
            role="admin" if user.is_admin else "user",
        )
        return user, token

    async def get_user_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.is_active == True)
        )
        return result.scalar_one_or_none()

    async def update_profile(self, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        await self.db.flush()
        return user
