from __future__ import annotations

from pydantic import BaseModel, Field


class WechatLogin(BaseModel):
    """微信小程序登录请求."""
    code: str = Field(..., min_length=1, description="微信登录临时code")
    nick_name: str | None = Field(None, max_length=64, description="用户昵称")
    avatar_url: str | None = Field(None, max_length=512, description="头像URL")


class PasswordLogin(BaseModel):
    """用户名密码登录."""
    username: str = Field(..., min_length=2, max_length=64, description="用户名")
    password: str = Field(..., min_length=4, max_length=128, description="密码")


class UserCreate(BaseModel):
    """管理员创建用户."""
    username: str = Field(..., min_length=2, max_length=64, description="用户名")
    password: str = Field(..., min_length=4, max_length=128, description="密码")
    nickname: str | None = Field(None, max_length=64, description="昵称")
    role: str = Field(default="user", pattern=r"^(admin|chef|user)$", description="角色")


class UserUpdate(BaseModel):
    """更新用户信息."""
    nickname: str | None = Field(None, max_length=64)
    avatar_url: str | None = Field(None, max_length=50000)
    phone: str | None = Field(None, max_length=20)
    bio: str | None = Field(None, max_length=256)
    role: str | None = Field(None, pattern=r"^(admin|chef|user)$")
    is_active: bool | None = None
    password: str | None = Field(None, min_length=4, max_length=128, description="新密码")


class UserOut(BaseModel):
    """用户信息输出."""
    id: int
    username: str | None = None
    nickname: str | None = None
    avatar_url: str | None = None
    phone: str | None = None
    bio: str | None = None
    role: str = "user"
    is_active: bool = True

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    """登录响应."""
    access_token: str
    token_type: str = "bearer"
    user: UserOut
