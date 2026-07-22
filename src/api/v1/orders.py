from __future__ import annotations

import json
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import get_current_user
from src.api.response import success, paginated
from src.core.database import get_db
from src.core.exceptions import BusinessError, NotFoundError
from src.models.dish import Dish
from src.models.order import Order, OrderItem
from src.models.user import User
from src.schemas.order import OrderCreate, OrderOut, OrderList, OrderItemOut

router = APIRouter()


def _generate_order_no() -> str:
    """生成订单编号：时间戳 + 随机数."""
    import random
    import time
    ts = int(time.time() * 1000)
    rand = random.randint(1000, 9999)
    return f"ORD{ts}{rand}"


@router.post("")
async def create_order(
    order_in: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建订单."""
    total_price = Decimal("0.00")
    order_items = []

    for item in order_in.items:
        # 查询菜品
        result = await db.execute(
            select(Dish).where(Dish.id == item.dish_id, Dish.status == "active")
        )
        dish = result.scalar_one_or_none()
        if dish is None:
            raise NotFoundError(message=f"菜品ID {item.dish_id} 不存在或已下架")

        if dish.price is None:
            raise BusinessError(message=f"菜品 '{dish.name}' 尚未定价")

        unit_price = dish.price * Decimal(str(item.quantity))
        total_price += unit_price

        # 校验排除的材料是否属于该菜品
        if item.excluded_material_ids:
            valid_material_ids = {m.id for m in dish.materials}
            invalid_ids = set(item.excluded_material_ids) - valid_material_ids
            if invalid_ids:
                raise BusinessError(
                    message=f"菜品 '{dish.name}' 不包含材料ID: {invalid_ids}"
                )

        order_items.append(
            OrderItem(
                dish_id=dish.id,
                dish_name=dish.name,
                quantity=item.quantity,
                unit_price=dish.price,
                excluded_material_ids=json.dumps(item.excluded_material_ids, ensure_ascii=False),
            )
        )
        # 更新销量
        dish.sales_count = (dish.sales_count or 0) + item.quantity

    order = Order(
        order_no=_generate_order_no(),
        user_id=current_user.id,
        status="pending",
        total_price=total_price,
        note=order_in.note,
        items=order_items,
    )
    db.add(order)
    await db.flush()

    return success(data=OrderOut.model_validate(order), message="下单成功")


@router.get("")
async def list_orders(
    status: str | None = Query(None, pattern=r"^(pending|confirmed|preparing|completed|cancelled)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的订单列表."""
    query = select(Order).where(Order.user_id == current_user.id)

    if status:
        query = query.where(Order.status == status)

    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = (
        query
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    orders = result.scalars().all()

    items = []
    for o in orders:
        items.append(OrderList(
            id=o.id,
            order_no=o.order_no,
            status=o.status,
            total_price=o.total_price,
            item_count=len(o.items) if o.items else 0,
            created_at=o.created_at,
        ))

    return paginated(items=items, total=total, page=page, page_size=page_size)


@router.get("/{order_id}")
async def get_order_detail(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取订单详情."""
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id, Order.user_id == current_user.id)
        .options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise NotFoundError(message="订单不存在")

    return success(data=OrderOut.model_validate(order))


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消订单（仅待处理状态的订单可取消）."""
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == current_user.id)
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise NotFoundError(message="订单不存在")

    if order.status != "pending":
        raise BusinessError(message="仅待处理状态的订单可以取消")

    order.status = "cancelled"
    await db.flush()

    return success(data=OrderOut.model_validate(order), message="订单已取消")
