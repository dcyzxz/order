from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PendingDishCreate(BaseModel):
    """用户提交待定价菜品."""
    name: str = Field(..., min_length=1, max_length=64, description="菜品名称")
    description: str | None = Field(None, description="菜品描述")
    image_url: str | None = Field(None, max_length=50000, description="参考图片URL")
    suggested_price: Decimal | None = Field(None, ge=0, decimal_places=2, description="建议价格")


class PendingDishReview(BaseModel):
    """管理员审核待定价菜品."""
    status: str = Field(..., pattern=r"^(approved|rejected)$", description="审核结果")
    admin_price: Decimal | None = Field(None, ge=0, decimal_places=2, description="管理员定价")
    admin_note: str | None = Field(None, description="管理员备注")
    category_id: int | None = Field(None, description="分配的分类ID")


class PendingDishOut(BaseModel):
    """待定价菜品输出."""
    id: int
    user_id: int
    user_name: str | None = None
    name: str
    description: str | None = None
    image_url: str | None = None
    suggested_price: Decimal | None = None
    status: str
    admin_price: Decimal | None = None
    admin_note: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
