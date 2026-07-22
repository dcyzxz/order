from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    """创建菜品分类."""
    name: str = Field(..., min_length=1, max_length=32, description="分类名称")
    sort_order: int = Field(default=0, ge=0, description="排序序号")


class CategoryUpdate(BaseModel):
    """更新菜品分类."""
    name: str | None = Field(None, min_length=1, max_length=32)
    sort_order: int | None = Field(None, ge=0)


class CategoryOut(BaseModel):
    """分类信息输出."""
    id: int
    name: str
    sort_order: int
    is_active: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
