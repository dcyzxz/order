from __future__ import annotations

from decimal import Decimal

from sqlalchemy import String, Numeric, Integer, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.mixins import TimestampMixin


class DishCategory(Base):
    """菜品-分类 多对多关联表"""
    __tablename__ = "dish_categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dish_id: Mapped[int] = mapped_column(Integer, ForeignKey("dishes.id", ondelete="CASCADE"), comment="菜品ID")
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), comment="分类ID")


class Dish(TimestampMixin, Base):
    """菜品模型"""

    __tablename__ = "dishes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="菜品名称")
    description: Mapped[str | None] = mapped_column(Text, comment="菜品描述")
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="定价")
    image_url: Mapped[str | None] = mapped_column(String(512), comment="图片URL")
    category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("categories.id"), comment="分类ID")
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        comment="状态: active=已上架, inactive=已下架, pending_price=待定价",
    )
    is_recommended: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否推荐")
    sales_count: Mapped[int] = mapped_column(Integer, default=0, comment="销量")

    # Relationships
    category = relationship("Category", back_populates="dishes", lazy="selectin")
    materials = relationship("Material", secondary="dish_materials", back_populates="dishes", lazy="selectin")
    order_items = relationship("OrderItem", back_populates="dish", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Dish(id={self.id}, name='{self.name}', status='{self.status}')>"
