from __future__ import annotations

from pydantic import BaseModel, Field


class WechatLogin(BaseModel):
    """微信小程序登录请求."""
    code: str = Field(..., min_length=1, description="微信登录临时code")
    nick_name: str | None = Field(None, max_length=64, description="用户昵称")
    avatar_url: str | None = Field(None, max_length=512, description="头像URL")


class UserCreate(BaseModel):
    """创建用户."""
    openid: str = Field(..., min_length=1, max_length=128)
    nickname: str | None = Field(None, max_length=64)
    avatar_url: str | None = Field(None, max_length=512)
    phone: str | None = Field(None, max_length=20)


class UserUpdate(BaseModel):
    """更新用户信息."""
    nickname: str | None = Field(None, max_length=64)
    avatar_url: str | None = Field(None, max_length=512)
    phone: str | None = Field(None, max_length=20)


class UserOut(BaseModel):
    """用户信息输出."""
    id: int
    openid: str
    nickname: str | None = None
    avatar_url: str | None = None
    phone: str | None = None
    is_admin: bool = False

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    """登录响应."""
    access_token: str
    token_type: str = "bearer"
    user: UserOut
