from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.response import success, paginated
from src.core.database import get_db
from src.core.exceptions import NotFoundError
from src.models.category import Category
from src.models.dish import Dish, DishCategory
from src.models.material import Material, DishMaterial
from src.schemas.dish import DishOut, DishList
from src.schemas.material import MaterialOut
from src.schemas.category import CategoryOut
from src.schemas.pending_dish import PendingDishCreate, PendingDishOut
from src.api.deps import get_current_user
from src.models.user import User
from src.models.pending_dish import PendingDish

router = APIRouter()


@router.get("/categories")
async def list_categories(
    db: AsyncSession = Depends(get_db),
):
    """获取菜品分类列表."""
    result = await db.execute(
        select(Category).where(Category.is_active == True).order_by(Category.sort_order)
    )
    categories = result.scalars().all()
    return success(
        data=[CategoryOut.model_validate(c) for c in categories],
    )


@router.get("/dishes")
async def list_dishes(
    category_id: int | None = Query(None, description="按分类筛选"),
    keyword: str | None = Query(None, max_length=50, description="搜索关键词"),
    recommended: bool | None = Query(None, description="仅推荐"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取菜品列表（仅返回已上架的菜品）."""
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

    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页
    query = query.order_by(Dish.is_recommended.desc(), Dish.sales_count.desc(), Dish.id)
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    dishes = result.scalars().all()

    items = []
    for d in dishes:
        items.append(DishList(
            id=d.id,
            name=d.name,
            price=d.price,
            image_url=d.image_url,
            category_id=d.category_id,
            category_name=d.category.name if d.category else None,
            status=d.status,
            is_recommended=d.is_recommended,
            sales_count=d.sales_count,
        ))

    return paginated(items=items, total=total, page=page, page_size=page_size)


@router.get("/dishes/{dish_id}")
async def get_dish_detail(
    dish_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取菜品详情（含材料清单）."""
    result = await db.execute(
        select(Dish)
        .where(Dish.id == dish_id, Dish.status == "active")
        .options(selectinload(Dish.category), selectinload(Dish.materials))
    )
    dish = result.scalar_one_or_none()
    if dish is None:
        raise NotFoundError(message="菜品不存在或已下架")

    # 获取多分类
    cat_result = await db.execute(
        select(DishCategory).where(DishCategory.dish_id == dish_id)
    )
    cat_ids = [dc.category_id for dc in cat_result.scalars().all()]

    return success(data=DishOut(
        id=dish.id,
        name=dish.name,
        description=dish.description,
        price=dish.price,
        image_url=dish.image_url,
        category_id=dish.category_id,
        category_name=dish.category.name if dish.category else None,
        category_ids=cat_ids,
        status=dish.status,
        is_recommended=dish.is_recommended,
        sales_count=dish.sales_count,
        materials=[MaterialOut.model_validate(m) for m in dish.materials],
        created_at=dish.created_at,
    ))


@router.get("/materials")
async def list_materials(
    db: AsyncSession = Depends(get_db),
):
    """获取所有材料清单（用于用户勾选排除）."""
    result = await db.execute(select(Material).order_by(Material.category, Material.name))
    materials = result.scalars().all()
    return success(data=[MaterialOut.model_validate(m) for m in materials])


@router.post("/pending-dishes")
async def submit_pending_dish(
    pending: PendingDishCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """用户提交菜单中没有的菜（待定价）."""
    dish = PendingDish(
        user_id=current_user.id,
        name=pending.name,
        description=pending.description,
        image_url=pending.image_url,
        suggested_price=pending.suggested_price,
        status="pending_price",
    )
    db.add(dish)
    await db.flush()

    return success(
        data=PendingDishOut.model_validate(dish),
        message="菜品已提交，等待管理员审核定价",
    )


@router.get("/pending-dishes")
async def list_my_pending_dishes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查看自己提交的待定价菜品."""
    result = await db.execute(
        select(PendingDish)
        .where(PendingDish.user_id == current_user.id)
        .order_by(PendingDish.created_at.desc())
    )
    dishes = result.scalars().all()
    return success(data=[PendingDishOut.model_validate(d) for d in dishes])
