from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from src.schemas.material import MaterialOut


class DishCreate(BaseModel):
    """创建菜品."""
    name: str = Field(..., min_length=1, max_length=64, description="菜品名称")
    description: str | None = Field(None, description="菜品描述")
    price: Decimal | None = Field(None, ge=0, decimal_places=2, description="定价")
    image_url: str | None = Field(None, max_length=50000, description="图片URL")
    category_id: int | None = Field(None, description="主分类ID")
    category_ids: list[int] = Field(default_factory=list, description="所有分类ID")
    material_ids: list[int] = Field(default_factory=list, description="关联材料ID列表")
    is_recommended: bool = False


class DishUpdate(BaseModel):
    """更新菜品."""
    name: str | None = Field(None, min_length=1, max_length=64)
    description: str | None = None
    price: Decimal | None = Field(None, ge=0, decimal_places=2)
    image_url: str | None = None
    category_id: int | None = None
    category_ids: list[int] | None = None
    status: str | None = Field(None, pattern=r"^(active|inactive|pending_price)$")
    material_ids: list[int] | None = None
    is_recommended: bool | None = None


class DishOut(BaseModel):
    """菜品信息输出（含材料清单）."""
    id: int
    name: str
    description: str | None = None
    price: Decimal | None = None
    image_url: str | None = None
    category_id: int | None = None
    category_name: str | None = None
    category_ids: list[int] = Field(default_factory=list)
    status: str = "active"
    is_recommended: bool = False
    sales_count: int = 0
    materials: list[MaterialOut] = Field(default_factory=list)
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class DishList(BaseModel):
    """菜品列表项."""
    id: int
    name: str
    price: Decimal | None = None
    image_url: str | None = None
    category_id: int | None = None
    category_name: str | None = None
    status: str
    is_recommended: bool = False
    sales_count: int = 0

    model_config = {"from_attributes": True}
