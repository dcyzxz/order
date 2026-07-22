from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.category import Category
from src.models.dish import Dish
from src.models.material import Material, DishMaterial


@pytest.fixture
async def seed_data(db_session: AsyncSession) -> None:
    """Seed test data for menu tests."""
    # Create category
    cat = Category(name="热菜", sort_order=1)
    db_session.add(cat)
    await db_session.flush()

    # Create materials
    pork = Material(name="猪肉", category="肉类")
    salt = Material(name="盐", category="调料")
    db_session.add_all([pork, salt])
    await db_session.flush()

    # Create dish
    dish = Dish(
        name="回锅肉",
        description="经典川菜",
        price=38.00,
        category_id=cat.id,
        status="active",
        is_recommended=True,
    )
    db_session.add(dish)
    await db_session.flush()

    # Link materials
    db_session.add_all([
        DishMaterial(dish_id=dish.id, material_id=pork.id),
        DishMaterial(dish_id=dish.id, material_id=salt.id),
    ])
    await db_session.flush()


@pytest.mark.anyio
async def test_list_categories(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test listing categories."""
    cat = Category(name="冷菜", sort_order=2)
    db_session.add(cat)
    await db_session.flush()

    response = await client.get("/api/v1/menu/categories")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert len(data["data"]) >= 1
    assert data["data"][0]["name"] == "冷菜"


@pytest.mark.anyio
async def test_list_dishes(client: AsyncClient, seed_data) -> None:
    """Test listing active dishes."""
    response = await client.get("/api/v1/menu/dishes")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["total"] == 1
    assert data["data"]["items"][0]["name"] == "回锅肉"


@pytest.mark.anyio
async def test_list_dishes_filter_by_category(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test filtering dishes by category."""
    cat = Category(name="汤类", sort_order=3)
    db_session.add(cat)
    await db_session.flush()

    dish1 = Dish(name="紫菜蛋花汤", price=15.00, category_id=cat.id, status="active")
    dish2 = Dish(name="番茄蛋汤", price=12.00, category_id=cat.id, status="active")
    db_session.add_all([dish1, dish2])
    await db_session.flush()

    response = await client.get(f"/api/v1/menu/dishes?category_id={cat.id}")
    data = response.json()
    assert data["data"]["total"] == 2


@pytest.mark.anyio
async def test_get_dish_detail(client: AsyncClient, seed_data) -> None:
    """Test getting dish details with materials."""
    response = await client.get("/api/v1/menu/dishes/1")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == "回锅肉"
    assert len(data["data"]["materials"]) == 2


@pytest.mark.anyio
async def test_get_dish_not_found(client: AsyncClient) -> None:
    """Test getting non-existent dish returns 404."""
    response = await client.get("/api/v1/menu/dishes/99999")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_list_materials(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test listing all materials."""
    db_session.add_all([
        Material(name="辣椒", category="蔬菜"),
        Material(name="酱油", category="调料"),
    ])
    await db_session.flush()

    response = await client.get("/api/v1/menu/materials")
    data = response.json()
    assert data["code"] == 200
    assert len(data["data"]) >= 2
