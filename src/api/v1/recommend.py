from __future__ import annotations

import random
from collections import Counter
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
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

# Simple knowledge base
GREETING_RESPONSES = [
    "你好呀！今天想吃点什么？我可以帮你推荐哦 🍽️",
    "嗨！肚子饿了吗？告诉我你想吃什么口味的~",
    "欢迎！让我看看今天有什么好吃的 🤗",
    "来啦！想吃什么跟我说，我给你推荐~",
]

FALLBACK_RESPONSES = [
    "唔，我没太懂你想吃什么 🤔 你可以说「推荐」让我来选，或者说「想吃肉」「想吃辣的」之类的",
    "不太明白呢～试试说「随便吃点」或者告诉我你想吃什么口味的？",
    "我还没学会这个 😅 你可以说「推荐」或者「随便」让我帮你选菜",
]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=200)


class ChatResponse(BaseModel):
    reply: str
    dishes: list[dict[str, Any]] = []


def _match_keyword(msg: str, keywords: list[str]) -> bool:
    return any(k in msg for k in keywords)


async def _get_recommended_dishes(
    db: AsyncSession,
    user_id: int | None = None,
    category_ids: list[int] | None = None,
    limit: int = 5,
) -> list[Dish]:
    query = select(Dish).where(Dish.status == "active").options(
        selectinload(Dish.materials), selectinload(Dish.category)
    )

    if category_ids:
        query = query.where(Dish.category_id.in_(category_ids))

    query = query.order_by(Dish.is_recommended.desc(), Dish.sales_count.desc())
    result = await db.execute(query)
    dishes = result.scalars().all()

    # Exclude what user ordered before if available
    if user_id:
        history = await db.execute(
            select(OrderItem).join(Order).where(
                Order.user_id == user_id, Order.status != "cancelled"
            )
        )
        ordered_ids = {item.dish_id for item in history.scalars().all()}
        new_dishes = [d for d in dishes if d.id not in ordered_ids]
        if new_dishes:
            return new_dishes[:limit]

    return dishes[:limit]


@router.post("/chat")
async def chat(
    chat_req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI 对话式点餐助手."""
    msg = chat_req.message.strip()
    reply = ""
    dishes = []
    user_id = current_user.id

    # 1. Greeting
    if _match_keyword(msg, ["你好", "嗨", "hello", "hi", "在吗", "在不在", "开始"]):
        reply = random.choice(GREETING_RESPONSES)
        dishes = await _get_recommended_dishes(db, user_id, limit=3)

    # 2. 随便/随机
    elif _match_keyword(msg, ["随便", "随机", "不知道", "有啥吃", "推荐"]):
        all_dishes = await _get_recommended_dishes(db, user_id, limit=20)
        if all_dishes:
            dishes = random.sample(all_dishes, min(3, len(all_dishes)))
            reply = "那我来帮你选！试试这些怎么样？ 🎲"
        else:
            reply = "暂时没有可推荐的菜品 😅"

    # 3. 想吃肉类/海鲜/蔬菜等
    elif _match_keyword(msg, ["肉", "猪", "牛", "羊", "鸡", "鸭"]):
        reply = "想吃肉呀！这些荤菜推荐给你 🥩"
        dishes = await _get_recommended_dishes(db, user_id, limit=5)

    elif _match_keyword(msg, ["海鲜", "鱼", "虾", "蟹", "贝"]):
        reply = "海鲜不错！看看这些 🦐"
        dishes = await _get_recommended_dishes(db, user_id, limit=5)

    elif _match_keyword(msg, ["素", "蔬菜", "青菜", "清淡"]):
        reply = "想吃清淡的，这些素菜很适合 🥬"
        dishes = await _get_recommended_dishes(db, user_id, limit=5)

    elif _match_keyword(msg, ["辣", "麻辣", "香辣", "重口味"]):
        reply = "无辣不欢！这些够味 🌶️"
        dishes = await _get_recommended_dishes(db, user_id, limit=5)

    elif _match_keyword(msg, ["汤", "羹"]):
        reply = "来碗汤暖暖胃 🍲"
        dishes = await _get_recommended_dishes(db, user_id, limit=5)

    # 4. 便宜的/贵的
    elif _match_keyword(msg, ["便宜", "实惠", "经济"]):
        reply = "经济实惠的选择来啦 💰"
        result = await db.execute(
            select(Dish).where(Dish.status == "active", Dish.price < 30)
            .order_by(Dish.price).limit(5)
        )
        dishes = list(result.scalars().all())

    elif _match_keyword(msg, ["贵", "豪华", "好点的", "大餐"]):
        reply = "今天吃顿好的！这些硬菜安排上 🎉"
        result = await db.execute(
            select(Dish).where(Dish.status == "active", Dish.price >= 50)
            .order_by(Dish.price.desc()).limit(5)
        )
        dishes = list(result.scalars().all())

    # 5. Fallback - general recommendations
    else:
        reply = random.choice(FALLBACK_RESPONSES)
        dishes = await _get_recommended_dishes(db, user_id, limit=3)

    return success(data=ChatResponse(
        reply=reply,
        dishes=[
            DishOut.model_validate(d).model_dump(mode="json") for d in dishes if d
        ],
    ))
