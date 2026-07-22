from __future__ import annotations

from pydantic import BaseModel, Field


class MaterialCreate(BaseModel):
    """创建材料."""
    name: str = Field(..., min_length=1, max_length=32, description="材料名称")
    category: str | None = Field(None, max_length=32, description="材料分类")
    description: str | None = Field(None, description="材料说明")
    is_allergen: bool = False


class MaterialUpdate(BaseModel):
    """更新材料."""
    name: str | None = Field(None, min_length=1, max_length=32)
    category: str | None = None
    description: str | None = None
    is_allergen: bool | None = None


class MaterialOut(BaseModel):
    """材料信息输出."""
    id: int
    name: str
    category: str | None = None
    description: str | None = None
    is_allergen: bool = False

    model_config = {"from_attributes": True}
