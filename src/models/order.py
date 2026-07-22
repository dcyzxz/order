from __future__ import annotations

from decimal import Decimal

from sqlalchemy import String, Numeric, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.mixins import TimestampMixin


class Order(TimestampMixin, Base):
    """订单模型"""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, comment="订单编号")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        comment="状态: pending=待处理, confirmed=已确认, preparing=制作中, completed=已完成, cancelled=已取消",
    )
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, comment="总价")
    note: Mapped[str | None] = mapped_column(Text, comment="订单备注")

    # Relationships
    user = relationship("User", back_populates="orders", lazy="selectin")
    items = relationship("OrderItem", back_populates="order", lazy="selectin", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, order_no='{self.order_no}', status='{self.status}')>"


class OrderItem(Base):
    """订单明细模型"""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    dish_id: Mapped[int] = mapped_column(Integer, ForeignKey("dishes.id"), nullable=False, comment="菜品ID")
    dish_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="下单时的菜品名称")
    quantity: Mapped[int] = mapped_column(Integer, default=1, comment="数量")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="单价")
    excluded_material_ids: Mapped[str | None] = mapped_column(
        Text, comment="排除的材料ID列表(JSON数组)", default=None
    )

    # Relationships
    order = relationship("Order", back_populates="items", lazy="selectin")
    dish = relationship("Dish", back_populates="order_items", lazy="selectin")

    def __repr__(self) -> str:
        return f"<OrderItem(id={self.id}, dish='{self.dish_name}', qty={self.quantity})>"
