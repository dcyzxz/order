from __future__ import annotations

from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.mixins import TimestampMixin


class Material(TimestampMixin, Base):
    """材料/食材模型"""

    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(32), nullable=False, comment="材料名称")
    category: Mapped[str | None] = mapped_column(String(32), comment="材料分类(如: 肉类,蔬菜,调料)")
    description: Mapped[str | None] = mapped_column(Text, comment="材料说明")
    is_allergen: Mapped[bool] = mapped_column(default=False, comment="是否为常见过敏原")

    # Relationships
    dishes = relationship("Dish", secondary="dish_materials", back_populates="materials", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Material(id={self.id}, name='{self.name}')>"


class DishMaterial(Base):
    """菜品-材料 多对多关联表"""

    __tablename__ = "dish_materials"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dish_id: Mapped[int] = mapped_column(Integer, ForeignKey("dishes.id", ondelete="CASCADE"), comment="菜品ID")
    material_id: Mapped[int] = mapped_column(Integer, ForeignKey("materials.id", ondelete="CASCADE"), comment="材料ID")
