from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.api.response import success
from src.core.database import get_db
from src.core.exceptions import AuthError, BusinessError
from src.core.security import create_access_token, hash_password, verify_password
from src.models.user import User
from src.schemas.user import UserUpdate, UserOut, LoginResponse, PasswordLogin

router = APIRouter()


@router.post("/login")
async def password_login(
    login_req: PasswordLogin,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """用户名密码登录."""
    # 查找用户
    result = await db.execute(
        select(User).where(User.username == login_req.username, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise AuthError(message="用户名或密码错误")

    if not user.password_hash or not verify_password(login_req.password, user.password_hash):
        raise AuthError(message="用户名或密码错误")

    # 生成 JWT
    token = create_access_token(subject=str(user.id), role=user.role)

    return success(
        data=LoginResponse(
            access_token=token,
            user=UserOut.model_validate(user),
        ),
    )


@router.get("/me")
async def get_profile(
    current_user: User = Depends(get_current_user),
) -> dict:
    """获取当前用户信息."""
    return success(data=UserOut.model_validate(current_user))


@router.put("/me")
async def update_profile(
    update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """更新当前用户信息."""
    if update.nickname is not None:
        current_user.nickname = update.nickname
    if update.avatar_url is not None:
        current_user.avatar_url = update.avatar_url
    if update.phone is not None:
        import re
        if update.phone and not re.match(r"^1\d{10}$", update.phone):
            raise BusinessError(message="手机号格式不正确")
        current_user.phone = update.phone

    await db.flush()
    return success(data=UserOut.model_validate(current_user))
