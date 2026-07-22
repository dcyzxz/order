from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import BusinessError, NotFoundError
from src.core.logger import get_logger
from src.models.dish import Dish
from src.models.pending_dish import PendingDish

logger = get_logger(__name__)


class PricingService:
    """定价审核相关业务逻辑."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_pending_dishes(
        self,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[PendingDish], int]:
        query = select(PendingDish).options(selectinload(PendingDish.user))

        if status:
            query = query.where(PendingDish.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = (
            query
            .order_by(PendingDish.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def review_pending_dish(
        self,
        pending_id: int,
        admin_id: int,
        status: str,
        admin_price=None,
        admin_note: str | None = None,
        category_id: int | None = None,
    ) -> PendingDish:
        result = await self.db.execute(
            select(PendingDish).where(PendingDish.id == pending_id)
        )
        pending = result.scalar_one_or_none()
        if pending is None:
            raise NotFoundError(message="待定价菜品不存在")
        if pending.status != "pending_price":
            raise BusinessError(message="该菜品已被审核")

        pending.status = status
        pending.admin_id = admin_id
        pending.admin_note = admin_note

        if status == "approved":
            if admin_price is None:
                raise BusinessError(message="审核通过时必须设置定价")
            pending.admin_price = admin_price

            # 创建正式菜品
            dish = Dish(
                name=pending.name,
                description=pending.description,
                image_url=pending.image_url,
                price=admin_price,
                category_id=category_id,
                status="active",
            )
            self.db.add(dish)

        await self.db.flush()

        logger.info(
            "PendingDish reviewed",
            extra={
                "pending_id": pending_id,
                "status": status,
                "admin_id": admin_id,
            },
        )
        return pending
