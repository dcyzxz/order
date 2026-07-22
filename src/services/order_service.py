from __future__ import annotations

import json
import random
import time
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import BusinessError, NotFoundError
from src.models.dish import Dish
from src.models.order import Order, OrderItem
from src.schemas.order import OrderCreate


class OrderService:
    """订单相关业务逻辑."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _generate_order_no() -> str:
        ts = int(time.time() * 1000)
        rand = random.randint(1000, 9999)
        return f"ORD{ts}{rand}"

    async def create_order(self, user_id: int, order_in: OrderCreate) -> Order:
        total_price = Decimal("0.00")
        order_items = []

        for item in order_in.items:
            result = await self.db.execute(
                select(Dish)
                .where(Dish.id == item.dish_id, Dish.status == "active")
                .options(selectinload(Dish.materials))
            )
            dish = result.scalar_one_or_none()
            if dish is None:
                raise NotFoundError(message=f"菜品ID {item.dish_id} 不存在或已下架")
            if dish.price is None:
                raise BusinessError(message=f"菜品 '{dish.name}' 尚未定价")

            unit_price = dish.price * Decimal(str(item.quantity))
            total_price += unit_price

            if item.excluded_material_ids:
                valid_ids = {m.id for m in dish.materials}
                invalid = set(item.excluded_material_ids) - valid_ids
                if invalid:
                    raise BusinessError(
                        message=f"菜品 '{dish.name}' 不包含材料ID: {invalid}"
                    )

            order_items.append(OrderItem(
                dish_id=dish.id,
                dish_name=dish.name,
                quantity=item.quantity,
                unit_price=dish.price,
                excluded_material_ids=json.dumps(item.excluded_material_ids, ensure_ascii=False),
            ))

            dish.sales_count = (dish.sales_count or 0) + item.quantity

        order = Order(
            order_no=self._generate_order_no(),
            user_id=user_id,
            status="pending",
            total_price=total_price,
            note=order_in.note,
            items=order_items,
        )
        self.db.add(order)
        await self.db.flush()
        return order

    async def list_user_orders(
        self,
        user_id: int,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Order], int]:
        query = select(Order).where(Order.user_id == user_id)
        if status:
            query = query.where(Order.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = (
            query
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_order_detail(self, order_id: int, user_id: int) -> Order:
        result = await self.db.execute(
            select(Order)
            .where(Order.id == order_id, Order.user_id == user_id)
            .options(selectinload(Order.items))
        )
        order = result.scalar_one_or_none()
        if order is None:
            raise NotFoundError(message="订单不存在")
        return order

    async def cancel_order(self, order_id: int, user_id: int) -> Order:
        result = await self.db.execute(
            select(Order).where(Order.id == order_id, Order.user_id == user_id)
        )
        order = result.scalar_one_or_none()
        if order is None:
            raise NotFoundError(message="订单不存在")
        if order.status != "pending":
            raise BusinessError(message="仅待处理状态的订单可以取消")
        order.status = "cancelled"
        await self.db.flush()
        return order
