from __future__ import annotations

from collections import Counter
from random import sample

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import get_current_user
from src.api.response import success
from src.core.database import get_db
from src.models.dish import Dish
from src.models.order import Order, OrderItem
from src.models.user import User
from src.schemas.dish import DishOut

router = APIRouter()


@router.get("")
async def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """基于用户历史订单推荐菜品."""

    # 1. 获取用户历史订单中的菜品ID
    history_items = await db.execute(
        select(OrderItem)
        .join(Order)
        .where(Order.user_id == current_user.id, Order.status != "cancelled")
    )
    history = history_items.scalars().all()

    # 统计用户常点的分类和菜品
    user_cat_ids: set[int] = set()
    ordered_dish_ids: set[int] = set()
    for item in history:
        ordered_dish_ids.add(item.dish_id)

    if ordered_dish_ids:
        # 找到用户点过的菜品所属分类
        history_dishes = await db.execute(
            select(Dish).where(Dish.id.in_(ordered_dish_ids))
        )
        for d in history_dishes.scalars().all():
            if d.category_id:
                user_cat_ids.add(d.category_id)

    # 2. 获取推荐菜品
    query = select(Dish).where(Dish.status == "active").options(selectinload(Dish.materials), selectinload(Dish.category))

    if user_cat_ids:
        # 优先推荐用户常点分类下的菜品
        query = query.where(Dish.category_id.in_(user_cat_ids))

    query = query.order_by(Dish.is_recommended.desc(), Dish.sales_count.desc())
    result = await db.execute(query)
    dishes = result.scalars().all()

    # 去重（排除用户点过的）
    recommended = [d for d in dishes if d.id not in ordered_dish_ids][:10]
    # 如果不够，补充用户点过的
    if len(recommended) < 5:
        repeat = [d for d in dishes if d.id in ordered_dish_ids]
        recommended.extend(repeat[:10 - len(recommended)])

    return success(data={
        "dishes": [DishOut.model_validate(d) for d in recommended[:10]],
        "total": len(dishes),
    })


@router.get("/random")
async def random_pick(
    db: AsyncSession = Depends(get_db),
):
    """随便吃点 - 随机推荐菜品."""
    result = await db.execute(
        select(Dish)
        .where(Dish.status == "active")
        .options(selectinload(Dish.materials), selectinload(Dish.category))
        .order_by(Dish.sales_count.desc())
    )
    dishes = result.scalars().all()
    if not dishes:
        return success(data={"dishes": []})

    picks = sample(dishes, min(3, len(dishes)))
    return success(data={
        "dishes": [DishOut.model_validate(d) for d in picks],
    })
