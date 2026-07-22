from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.api.response import success
from src.core.database import get_db
from src.core.exceptions import BusinessError
from src.models.user import User
from src.schemas.user import UserUpdate, UserOut, LoginResponse, WechatLogin

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def wechat_login(
    login_req: WechatLogin,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """
    微信小程序登录。
    注意：生产环境中应调用微信服务器验证 code，此处为简化实现。
    """
    # TODO: 生产环境应调用微信服务器验证 code 获取 openid
    # 模拟 openid（测试环境使用固定值）
    mock_openid = f"mock_openid_{login_req.code}"

    # 查找或创建用户
    result = await db.execute(select(User).where(User.openid == mock_openid))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            openid=mock_openid,
            nickname=login_req.nick_name,
            avatar_url=login_req.avatar_url,
        )
        db.add(user)
        await db.flush()

    # 生成 JWT
    from src.core.security import create_access_token
    token = create_access_token(subject=str(user.id), role="admin" if user.is_admin else "user")

    return LoginResponse(
        access_token=token,
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
async def get_profile(
    current_user: User = Depends(get_current_user),
) -> UserOut:
    """获取当前用户信息."""
    return UserOut.model_validate(current_user)


@router.put("/me", response_model=UserOut)
async def update_profile(
    update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """更新当前用户信息."""
    if update.nickname is not None:
        current_user.nickname = update.nickname
    if update.avatar_url is not None:
        current_user.avatar_url = update.avatar_url
    if update.phone is not None:
        # 简单手机号格式校验
        import re
        if update.phone and not re.match(r"^1\d{10}$", update.phone):
            raise BusinessError(message="手机号格式不正确")
        current_user.phone = update.phone

    await db.flush()
    return UserOut.model_validate(current_user)
