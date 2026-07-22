from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import NotFoundError
from src.models.category import Category
from src.models.dish import Dish
from src.models.material import Material


class MenuService:
    """菜单相关业务逻辑."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_categories(self) -> list[Category]:
        result = await self.db.execute(
            select(Category)
            .where(Category.is_active == True)
            .order_by(Category.sort_order)
        )
        return list(result.scalars().all())

    async def list_dishes(
        self,
        category_id: int | None = None,
        keyword: str | None = None,
        recommended: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Dish], int]:
        query = (
            select(Dish)
            .where(Dish.status == "active")
            .options(selectinload(Dish.category))
        )

        if category_id:
            query = query.where(Dish.category_id == category_id)
        if keyword:
            query = query.where(Dish.name.ilike(f"%{keyword}%"))
        if recommended:
            query = query.where(Dish.is_recommended == True)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = (
            query
            .order_by(Dish.is_recommended.desc(), Dish.sales_count.desc(), Dish.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_dish_detail(self, dish_id: int) -> Dish:
        result = await self.db.execute(
            select(Dish)
            .where(Dish.id == dish_id, Dish.status == "active")
            .options(selectinload(Dish.category), selectinload(Dish.materials))
        )
        dish = result.scalar_one_or_none()
        if dish is None:
            raise NotFoundError(message="菜品不存在或已下架")
        return dish

    async def get_all_materials(self) -> list[Material]:
        result = await self.db.execute(
            select(Material).order_by(Material.category, Material.name)
        )
        return list(result.scalars().all())
