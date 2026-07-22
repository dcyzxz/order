from __future__ import annotations

from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.category import Category
from src.models.dish import Dish
from src.models.material import Material, DishMaterial
from src.models.user import User


@pytest.fixture
async def seed_data(db_session: AsyncSession) -> dict:
    """Seed test data and return IDs."""
    cat = Category(name="热菜", sort_order=1)
    db_session.add(cat)
    await db_session.flush()

    pork = Material(name="猪肉", category="肉类")
    salt = Material(name="盐", category="调料")
    db_session.add_all([pork, salt])
    await db_session.flush()

    dish = Dish(name="回锅肉", description="经典川菜", price=38.00, category_id=cat.id, status="active")
    db_session.add(dish)
    await db_session.flush()

    db_session.add_all([
        DishMaterial(dish_id=dish.id, material_id=pork.id),
        DishMaterial(dish_id=dish.id, material_id=salt.id),
    ])

    # Create a test user
    user = User(openid="test_openid_for_orders", nickname="测试用户")
    db_session.add(user)
    await db_session.flush()

    return {"dish_id": dish.id, "user_id": user.id, "pork_id": pork.id, "salt_id": salt.id}


@pytest.fixture
async def auth_token(client: AsyncClient, db_session: AsyncSession, seed_data: dict) -> str:
    """Get auth token for the test user."""
    response = await client.post(
        "/api/v1/users/login",
        json={"code": "test_code_orders"},
    )
    data = response.json()
    return data["access_token"]


@pytest.fixture
async def auth_headers(auth_token: str) -> dict:
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.mark.anyio
async def test_create_order(client: AsyncClient, auth_headers: dict, seed_data: dict) -> None:
    """Test creating an order."""
    response = await client.post(
        "/api/v1/orders",
        json={
            "items": [
                {
                    "dish_id": seed_data["dish_id"],
                    "quantity": 2,
                    "excluded_material_ids": [seed_data["salt_id"]],
                },
            ],
            "note": "少放盐",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["status"] == "pending"
    assert data["data"]["total_price"] == 76.00
    assert len(data["data"]["items"]) == 1


@pytest.mark.anyio
async def test_create_order_without_auth(client: AsyncClient, seed_data: dict) -> None:
    """Test creating order without authentication."""
    response = await client.post(
        "/api/v1/orders",
        json={
            "items": [{"dish_id": seed_data["dish_id"], "quantity": 1}],
        },
    )
    assert response.status_code == 422  # FastAPI validation error for missing header


@pytest.mark.anyio
async def test_list_orders(client: AsyncClient, auth_headers: dict) -> None:
    """Test listing orders."""
    response = await client.get("/api/v1/orders", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200


@pytest.mark.anyio
async def test_cancel_order(client: AsyncClient, auth_headers: dict, seed_data: dict) -> None:
    """Test cancelling an order."""
    # Create order first
    create_resp = await client.post(
        "/api/v1/orders",
        json={"items": [{"dish_id": seed_data["dish_id"], "quantity": 1}]},
        headers=auth_headers,
    )
    order_id = create_resp.json()["data"]["id"]

    # Cancel
    cancel_resp = await client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers=auth_headers,
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["data"]["status"] == "cancelled"
