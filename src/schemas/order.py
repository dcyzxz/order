from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class OrderItemCreate(BaseModel):
    """创建订单明细."""
    dish_id: int = Field(..., ge=1, description="菜品ID")
    quantity: int = Field(default=1, ge=1, le=100, description="数量")
    excluded_material_ids: list[int] = Field(default_factory=list, description="排除的材料ID列表")


class OrderCreate(BaseModel):
    """创建订单."""
    items: list[OrderItemCreate] = Field(..., min_length=1, max_length=50, description="订单项")
    note: str | None = Field(None, max_length=500, description="订单备注")

    @field_validator("items")
    @classmethod
    def validate_items(cls, v: list[OrderItemCreate]) -> list[OrderItemCreate]:
        dish_ids = {item.dish_id for item in v}
        if len(dish_ids) != len(v):
            raise ValueError("订单中包含重复的菜品")
        return v


class OrderItemOut(BaseModel):
    """订单明细输出."""
    id: int
    dish_id: int
    dish_name: str
    quantity: int
    unit_price: Decimal
    excluded_material_ids: list[int] = []

    model_config = {"from_attributes": True}

    @field_validator("excluded_material_ids", mode="before")
    @classmethod
    def parse_excluded_materials(cls, v: str | list[int] | None) -> list[int]:
        if v is None:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        return []


class OrderOut(BaseModel):
    """订单信息输出."""
    id: int
    order_no: str
    user_id: int
    status: str
    total_price: Decimal
    note: str | None = None
    items: list[OrderItemOut] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class OrderList(BaseModel):
    """订单列表项."""
    id: int
    order_no: str
    status: str
    total_price: Decimal
    item_count: int = 0
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
