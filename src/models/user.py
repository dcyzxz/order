from __future__ import annotations

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.mixins import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    openid: Mapped[str | None] = mapped_column(String(128), unique=True, comment="微信openid")
    username: Mapped[str | None] = mapped_column(String(64), unique=True, comment="用户名")
    password_hash: Mapped[str | None] = mapped_column(String(128), comment="密码哈希")
    nickname: Mapped[str | None] = mapped_column(String(64), comment="昵称")
    avatar_url: Mapped[str | None] = mapped_column(String(512), comment="头像URL")
    phone: Mapped[str | None] = mapped_column(String(20), comment="手机号")
    role: Mapped[str] = mapped_column(String(20), default="user", comment="角色: admin/chef/user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")

    # Relationships
    orders = relationship("Order", back_populates="user", lazy="selectin")
    pending_dishes = relationship("PendingDish", back_populates="user", lazy="selectin", foreign_keys="PendingDish.user_id")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
