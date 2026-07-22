from __future__ import annotations

import json
import os
import uuid
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import get_admin_user, get_current_user, get_staff_user
from src.api.response import success, paginated
from src.core.database import get_db
from src.core.exceptions import BusinessError, NotFoundError
from src.core.security import hash_password
from src.models.category import Category
from src.models.dish import Dish, DishCategory
from src.models.material import Material, DishMaterial
from src.models.pending_dish import PendingDish
from src.models.order import Order
from src.models.pending_dish import PendingDish
from src.models.user import User
from src.schemas.category import CategoryCreate, CategoryUpdate, CategoryOut
from src.schemas.dish import DishCreate, DishUpdate, DishOut
from src.schemas.material import MaterialCreate, MaterialUpdate, MaterialOut
from src.schemas.order import OrderOut
from src.schemas.pending_dish import PendingDishCreate, PendingDishOut, PendingDishReview
from src.schemas.user import UserCreate as UserCreateSchema, UserUpdate as UserUpdateSchema, UserOut
from fastapi import UploadFile, File
import base64

router = APIRouter()


class BatchIds(BaseModel):
    ids: list[int]


# ==================== 文件上传 ====================

UPLOAD_DIR = Path(__file__).parent.parent.parent.parent / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    staff: User = Depends(get_staff_user),
):
    """上传图片（转为 base64 内嵌，不依赖外部存储）. """
    ext = os.path.splitext(file.filename or "image.jpg")[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
        raise BusinessError(message="仅支持 jpg/png/gif/webp 格式")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise BusinessError(message="文件大小不能超过 5MB")

    # 转为 base64 数据 URL
    mime = f"image/{ext[1:]}"
    if ext == ".jpg":
        mime = "image/jpeg"
    b64 = base64.b64encode(content).decode()
    data_url = f"data:{mime};base64,{b64}"

    # 同时也存一份到本地（某些场景备用）
    filename = f"{uuid.uuid4().hex}{ext}"
    with open(UPLOAD_DIR / filename, "wb") as f:
        f.write(content)

    return success(data={"url": data_url}, message="上传成功")


# ==================== 用户管理 ====================

@router.post("/users")
async def create_user(
    user_in: UserCreateSchema,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员创建用户."""
    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == user_in.username))
    if result.scalar_one_or_none():
        raise BusinessError(message="用户名已存在")

    user = User(
        username=user_in.username,
        password_hash=hash_password(user_in.password),
        nickname=user_in.nickname,
        role=user_in.role,
    )
    db.add(user)
    await db.flush()
    return success(data=UserOut.model_validate(user), message="用户创建成功")


@router.get("/users")
async def list_users(
    role: str | None = Query(None, pattern=r"^(admin|chef|user)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员查看用户列表."""
    query = select(User)
    if role:
        query = query.where(User.role == role)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()

    return paginated(items=[UserOut.model_validate(u) for u in users], total=total, page=page, page_size=page_size)


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_in: UserUpdateSchema,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员更新用户信息."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError(message="用户不存在")

    if user_in.nickname is not None:
        user.nickname = user_in.nickname
    if user_in.role is not None:
        user.role = user_in.role
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    if user_in.password is not None:
        user.password_hash = hash_password(user_in.password)

    await db.flush()
    return success(data=UserOut.model_validate(user), message="用户更新成功")


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员删除用户."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError(message="用户不存在")
    if user.id == admin.id:
        raise BusinessError(message="不能删除自己")

    # 先删除关联的订单和待定价菜品
    from src.models.order import Order
    orders = await db.execute(select(Order).where(Order.user_id == user_id))
    for o in orders.scalars().all():
        await db.delete(o)

    pendings = await db.execute(select(PendingDish).where(PendingDish.user_id == user_id))
    for p in pendings.scalars().all():
        await db.delete(p)

    # 也把该用户作为审核人的记录清掉
    admin_pendings = await db.execute(
        select(PendingDish).where(PendingDish.admin_id == user_id)
    )
    for p in admin_pendings.scalars().all():
        p.admin_id = None

    await db.delete(user)
    await db.flush()
    return success(message="用户已删除")


@router.post("/users/batch-delete")
async def batch_delete_users(
    body: BatchIds,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """批量删除用户."""
    for uid in body.ids:
        if uid == admin.id:
            continue
        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if user is None:
            continue
        # Clean up related records
        orders = await db.execute(select(Order).where(Order.user_id == uid))
        for o in orders.scalars().all():
            await db.delete(o)
        pendings = await db.execute(select(PendingDish).where(PendingDish.user_id == uid))
        for p in pendings.scalars().all():
            await db.delete(p)
        admin_ps = await db.execute(select(PendingDish).where(PendingDish.admin_id == uid))
        for p in admin_ps.scalars().all():
            p.admin_id = None
        await db.delete(user)
    await db.flush()
    return success(message=f"已删除 {len(body.ids)} 个用户")


# ==================== 菜品管理 ====================

@router.post("/dishes")
async def create_dish(
    dish_in: DishCreate,
    staff: User = Depends(get_staff_user),
    db: AsyncSession = Depends(get_db),
):
    """创建菜品（管理员/厨师）. """
    dish = Dish(
        name=dish_in.name,
        description=dish_in.description,
        price=dish_in.price,
        image_url=dish_in.image_url,
        category_id=dish_in.category_id,
        status="active" if dish_in.price else "pending_price",
        is_recommended=dish_in.is_recommended,
    )
    db.add(dish)
    await db.flush()

    # 关联材料
    if dish_in.material_ids:
        for mid in dish_in.material_ids:
            db.add(DishMaterial(dish_id=dish.id, material_id=mid))
    # 关联多分类
    all_cats = list(set(dish_in.category_ids or []))
    if dish_in.category_id and dish_in.category_id not in all_cats:
        all_cats.append(dish_in.category_id)
    for cid in all_cats:
        db.add(DishCategory(dish_id=dish.id, category_id=cid))
    await db.flush()

    # 重新查询以加载关系
    await db.refresh(dish, ["materials", "category"])
    # 手动加载多分类
    cat_ids = await _get_dish_category_ids(db, dish.id)
    return success(data=_dish_out_with_cats(dish, cat_ids), message="菜品创建成功")


async def _get_dish_category_ids(db: AsyncSession, dish_id: int) -> list[int]:
    result = await db.execute(
        select(DishCategory).where(DishCategory.dish_id == dish_id)
    )
    return [dc.category_id for dc in result.scalars().all()]


def _dish_out_with_cats(dish: Dish, cat_ids: list[int]) -> dict:
    d = DishOut.model_validate(dish).model_dump(mode="python")
    d["category_ids"] = cat_ids
    return d


@router.put("/dishes/{dish_id}")
async def update_dish(
    dish_id: int,
    dish_in: DishUpdate,
    staff: User = Depends(get_staff_user),
    db: AsyncSession = Depends(get_db),
):
    """更新菜品（管理员/厨师）. """
    result = await db.execute(
        select(Dish).where(Dish.id == dish_id).options(selectinload(Dish.materials))
    )
    dish = result.scalar_one_or_none()
    if dish is None:
        raise NotFoundError(message="菜品不存在")

    if dish_in.name is not None:
        dish.name = dish_in.name
    if dish_in.description is not None:
        dish.description = dish_in.description
    if dish_in.price is not None:
        dish.price = dish_in.price
    if dish_in.image_url is not None:
        dish.image_url = dish_in.image_url
    if dish_in.category_id is not None:
        dish.category_id = dish_in.category_id
    if dish_in.status is not None:
        dish.status = dish_in.status
    if dish_in.is_recommended is not None:
        dish.is_recommended = dish_in.is_recommended

    # 更新多分类
    if dish_in.category_ids is not None:
        old_cats = await db.execute(
            select(DishCategory).where(DishCategory.dish_id == dish_id)
        )
        for dc in old_cats.scalars().all():
            await db.delete(dc)
        all_cats = list(set(dish_in.category_ids))
        if dish_in.category_id and dish_in.category_id not in all_cats:
            all_cats.append(dish_in.category_id)
        for cid in all_cats:
            db.add(DishCategory(dish_id=dish_id, category_id=cid))

    # 更新材料关联
    if dish_in.material_ids is not None:
        # 删除旧关联
        old = await db.execute(
            select(DishMaterial).where(DishMaterial.dish_id == dish_id)
        )
        for dm in old.scalars().all():
            await db.delete(dm)
        # 添加新关联
        for mid in dish_in.material_ids:
            db.add(DishMaterial(dish_id=dish_id, material_id=mid))

    await db.flush()
    await db.refresh(dish, ["materials", "category"])
    cat_ids = await _get_dish_category_ids(db, dish_id)
    return success(data=_dish_out_with_cats(dish, cat_ids), message="菜品更新成功")


@router.delete("/dishes/{dish_id}")
async def delete_dish(
    dish_id: int,
    staff: User = Depends(get_staff_user),
    db: AsyncSession = Depends(get_db),
):
    """删除菜品（管理员/厨师）. """
    result = await db.execute(
        select(Dish).where(Dish.id == dish_id).options(selectinload(Dish.materials))
    )
    dish = result.scalar_one_or_none()
    if dish is None:
        raise NotFoundError(message="菜品不存在")
    await db.delete(dish)
    await db.flush()
    return success(message="菜品已删除")


@router.get("/dishes")
async def admin_list_dishes(
    status: str | None = Query(None, pattern=r"^(active|inactive|pending_price)$"),
    category_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    staff: User = Depends(get_staff_user),
    db: AsyncSession = Depends(get_db),
):
    """查看所有菜品（管理员/厨师）. """
    query = select(Dish).options(selectinload(Dish.category), selectinload(Dish.materials))

    if status:
        query = query.where(Dish.status == status)
    if category_id:
        query = query.where(Dish.category_id == category_id)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Dish.id.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    dishes = result.scalars().all()

    # 批量加载多分类
    dish_ids = [d.id for d in dishes]
    cat_rows = []
    if dish_ids:
        cat_rows = (await db.execute(
            select(DishCategory).where(DishCategory.dish_id.in_(dish_ids))
        )).scalars().all()
    cat_map = {}
    cat_name_map = {}
    for row in cat_rows:
        cat_map.setdefault(row.dish_id, []).append(row.category_id)
    # Get category names
    all_cat_ids = list(set(cid for ids in cat_map.values() for cid in ids))
    if all_cat_ids:
        cat_name_rows = await db.execute(select(Category).where(Category.id.in_(all_cat_ids)))
        cat_name_map = {c.id: c.name for c in cat_name_rows.scalars().all()}

    items = []
    for d in dishes:
        cat_ids = cat_map.get(d.id, [])
        items.append(DishOut(
            id=d.id,
            name=d.name,
            description=d.description,
            price=d.price,
            image_url=d.image_url,
            category_id=d.category_id,
            category_name=d.category.name if d.category else None,
            status=d.status,
            is_recommended=d.is_recommended,
            sales_count=d.sales_count,
            category_ids=cat_ids,
            category_names=[cat_name_map.get(cid, "") for cid in cat_ids],
            materials=[MaterialOut.model_validate(m) for m in (d.materials or [])],
            created_at=d.created_at,
        ))

    return paginated(items=items, total=total, page=page, page_size=page_size)


# ==================== 分类管理 ====================

@router.post("/categories")
async def create_category(
    cat_in: CategoryCreate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建菜品分类."""
    cat = Category(name=cat_in.name, sort_order=cat_in.sort_order)
    db.add(cat)
    await db.flush()
    return success(data=CategoryOut.model_validate(cat), message="分类创建成功")


@router.put("/categories/{category_id}")
async def update_category(
    category_id: int,
    cat_in: CategoryUpdate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新菜品分类."""
    result = await db.execute(select(Category).where(Category.id == category_id))
    cat = result.scalar_one_or_none()
    if cat is None:
        raise NotFoundError(message="分类不存在")

    if cat_in.name is not None:
        cat.name = cat_in.name
    if cat_in.sort_order is not None:
        cat.sort_order = cat_in.sort_order
    await db.flush()
    return success(data=CategoryOut.model_validate(cat), message="分类更新成功")


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员删除分类."""
    result = await db.execute(select(Category).where(Category.id == category_id))
    cat = result.scalar_one_or_none()
    if cat is None:
        raise NotFoundError(message="分类不存在")
    await db.delete(cat)
    await db.flush()
    return success(message="分类已删除")


@router.get("/categories")
async def admin_list_categories(
    staff: User = Depends(get_staff_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有分类（管理员/厨师）. """
    result = await db.execute(select(Category).order_by(Category.sort_order))
    cats = result.scalars().all()
    return success(data=[CategoryOut.model_validate(c) for c in cats])


# ==================== 材料管理 ====================

@router.post("/materials")
async def create_material(
    mat_in: MaterialCreate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建材料."""
    mat = Material(
        name=mat_in.name,
        category=mat_in.category,
        description=mat_in.description,
        is_allergen=mat_in.is_allergen,
    )
    db.add(mat)
    await db.flush()
    return success(data=MaterialOut.model_validate(mat), message="材料创建成功")


@router.put("/materials/{material_id}")
async def update_material(
    material_id: int,
    mat_in: MaterialUpdate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新材料."""
    result = await db.execute(select(Material).where(Material.id == material_id))
    mat = result.scalar_one_or_none()
    if mat is None:
        raise NotFoundError(message="材料不存在")

    if mat_in.name is not None:
        mat.name = mat_in.name
    if mat_in.category is not None:
        mat.category = mat_in.category
    if mat_in.description is not None:
        mat.description = mat_in.description
    if mat_in.is_allergen is not None:
        mat.is_allergen = mat_in.is_allergen
    await db.flush()
    return success(data=MaterialOut.model_validate(mat), message="材料更新成功")


@router.get("/materials")
async def admin_list_materials(
    staff: User = Depends(get_staff_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有材料（管理员/厨师）. """
    result = await db.execute(select(Material).order_by(Material.category, Material.name))
    mats = result.scalars().all()
    return success(data=[MaterialOut.model_validate(m) for m in mats])


@router.delete("/materials/{material_id}")
async def delete_material(
    material_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员删除材料."""
    result = await db.execute(select(Material).where(Material.id == material_id))
    mat = result.scalar_one_or_none()
    if mat is None:
        raise NotFoundError(message="材料不存在")
    await db.delete(mat)
    await db.flush()
    return success(message="材料已删除")


@router.post("/materials/batch-delete")
async def batch_delete_materials(
    body: BatchIds,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """批量删除材料."""
    result = await db.execute(select(Material).where(Material.id.in_(body.ids)))
    for mat in result.scalars().all():
        await db.delete(mat)
    await db.flush()
    return success(message=f"已删除 {len(body.ids)} 个材料")


# ==================== 订单管理 ====================

@router.get("/orders/chef")
async def chef_list_orders(
    status: str | None = Query(None, pattern=r"^(pending|confirmed|preparing|completed|cancelled)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    staff: User = Depends(get_staff_user),
    db: AsyncSession = Depends(get_db),
):
    """厨师/管理员查看订单."""
    query = select(Order).options(selectinload(Order.items), selectinload(Order.user))

    if status:
        query = query.where(Order.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    orders = result.scalars().all()
    # Populate excluded material names
    mat_result = await db.execute(select(Material))
    mat_map = {m.id: m.name for m in mat_result.scalars().all()}
    items = []
    for o in orders:
        order_dict = OrderOut.model_validate(o).model_dump(mode="python")
        for item in order_dict.get("items", []):
            if item.get("excluded_material_ids"):
                item["excluded_material_names"] = [mat_map.get(i, f"ID:{i}") for i in item["excluded_material_ids"]]
            else:
                item["excluded_material_names"] = []
        items.append(order_dict)
    return paginated(items=items, total=total, page=page, page_size=page_size)


@router.get("/orders")
async def admin_list_orders(
    status: str | None = Query(None, pattern=r"^(pending|confirmed|preparing|completed|cancelled)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员获取所有订单."""
    query = select(Order).options(selectinload(Order.items), selectinload(Order.user))

    if status:
        query = query.where(Order.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    orders = result.scalars().all()
    mat_result = await db.execute(select(Material))
    mat_map = {m.id: m.name for m in mat_result.scalars().all()}
    items = []
    for o in orders:
        order_dict = OrderOut.model_validate(o).model_dump(mode="python")
        for item in order_dict.get("items", []):
            if item.get("excluded_material_ids"):
                item["excluded_material_names"] = [mat_map.get(i, f"ID:{i}") for i in item["excluded_material_ids"]]
            else:
                item["excluded_material_names"] = []
        items.append(order_dict)
    return paginated(items=items, total=total, page=page, page_size=page_size)


@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    new_status: str = Query(..., pattern=r"^(confirmed|preparing|completed|cancelled)$"),
    staff: User = Depends(get_staff_user),
    db: AsyncSession = Depends(get_db),
):
    """更新订单状态（管理员/厨师）. """
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if order is None:
        raise NotFoundError(message="订单不存在")

    order.status = new_status
    await db.flush()
    return success(data=OrderOut.model_validate(order), message=f"订单状态已更新为 {new_status}")


@router.delete("/orders/{order_id}")
async def delete_order(
    order_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员删除订单."""
    result = await db.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise NotFoundError(message="订单不存在")

    await db.delete(order)
    await db.flush()
    return success(message="订单已删除")


@router.post("/orders/batch-delete")
async def batch_delete_orders(
    body: BatchIds,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """批量删除订单."""
    result = await db.execute(select(Order).where(Order.id.in_(body.ids)))
    for order in result.scalars().all():
        await db.delete(order)
    await db.flush()
    return success(message=f"已删除 {len(body.ids)} 个订单")


# ==================== 待定价菜品审核 ====================

@router.get("/pending-dishes")
async def admin_list_pending_dishes(
    status: str | None = Query(None, pattern=r"^(pending_price|approved|rejected)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员查看所有待定价菜品."""
    query = select(PendingDish).options(selectinload(PendingDish.user))

    if status:
        query = query.where(PendingDish.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(PendingDish.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    dishes = result.scalars().all()

    items = []
    for d in dishes:
        items.append(PendingDishOut(
            id=d.id,
            user_id=d.user_id,
            user_name=d.user.nickname if d.user else None,
            name=d.name,
            description=d.description,
            image_url=d.image_url,
            suggested_price=d.suggested_price,
            status=d.status,
            admin_price=d.admin_price,
            admin_note=d.admin_note,
            created_at=d.created_at,
        ))

    return paginated(items=items, total=total, page=page, page_size=page_size)


@router.post("/pending-dishes/{pending_id}/review")
async def review_pending_dish(
    pending_id: int,
    review: PendingDishReview,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员审核待定价菜品."""
    result = await db.execute(select(PendingDish).where(PendingDish.id == pending_id))
    pending = result.scalar_one_or_none()
    if pending is None:
        raise NotFoundError(message="待定价菜品不存在")

    if pending.status != "pending_price":
        raise BusinessError(message="该菜品已被审核")

    pending.status = review.status
    pending.admin_id = admin.id
    pending.admin_note = review.admin_note

    if review.status == "approved":
        if review.admin_price is None:
            raise BusinessError(message="审核通过时必须设置定价")
        pending.admin_price = review.admin_price

        # 创建正式菜品
        dish = Dish(
            name=pending.name,
            description=pending.description,
            image_url=pending.image_url,
            price=review.admin_price,
            category_id=review.category_id,
            status="active",
        )
        db.add(dish)

    await db.flush()

    # 记录变更日志
    from src.core.logger import get_logger
    logger = get_logger(__name__)
    logger.info(
        "PendingDish reviewed",
        extra={
            "pending_id": pending_id,
            "status": review.status,
            "admin_id": admin.id,
            "admin_price": str(review.admin_price) if review.admin_price else None,
        },
    )

    return success(
        data=PendingDishOut.model_validate(pending),
        message=f"菜品已{'审核通过' if review.status == 'approved' else '驳回'}",
    )


@router.delete("/pending-dishes/{pending_id}")
async def delete_pending_dish(
    pending_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员删除待定价菜品."""
    result = await db.execute(select(PendingDish).where(PendingDish.id == pending_id))
    pending = result.scalar_one_or_none()
    if pending is None:
        raise NotFoundError(message="待定价菜品不存在")
    await db.delete(pending)
    await db.flush()
    return success(message="已删除")
