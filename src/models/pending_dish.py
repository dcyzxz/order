from __future__ import annotations

from decimal import Decimal

from sqlalchemy import String, Numeric, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.mixins import TimestampMixin


class PendingDish(TimestampMixin, Base):
    """待定价菜品模型 - 用户提交菜单中没有的菜"""

    __tablename__ = "pending_dishes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, comment="提交用户ID")
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="菜品名称")
    description: Mapped[str | None] = mapped_column(Text, comment="菜品描述")
    image_url: Mapped[str | None] = mapped_column(Text, comment="参考图片URL")
    suggested_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="建议价格")
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending_price",
        comment="状态: pending_price=待定价, approved=已审核通过, rejected=已驳回",
    )
    admin_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="管理员定价")
    admin_note: Mapped[str | None] = mapped_column(Text, comment="管理员备注")
    admin_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), comment="审核管理员ID")

    # Relationships
    user = relationship("User", back_populates="pending_dishes", lazy="selectin", foreign_keys=[user_id])
    admin = relationship("User", foreign_keys=[admin_id], lazy="selectin")

    def __repr__(self) -> str:
        return f"<PendingDish(id={self.id}, name='{self.name}', status='{self.status}')>"
