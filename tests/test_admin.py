from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.core.security import create_access_token, hash_password


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user."""
    user = User(
        openid="admin_openid",
        username="admin",
        password_hash=hash_password("admin123"),
        nickname="管理员",
        role="admin",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def admin_token(admin_user: User) -> str:
    """Create admin JWT token."""
    return create_access_token(subject=str(admin_user.id), role="admin")


@pytest.fixture
async def admin_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.mark.anyio
async def test_admin_create_category(client: AsyncClient, admin_headers: dict) -> None:
    """Test admin creating a category."""
    response = await client.post(
        "/api/v1/admin/categories",
        json={"name": "测试分类", "sort_order": 1},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == "测试分类"


@pytest.mark.anyio
async def test_admin_create_dish(client: AsyncClient, admin_headers: dict, db_session: AsyncSession) -> None:
    """Test admin creating a dish with materials."""
    from src.models.material import Material
    mat = Material(name="测试材料")
    db_session.add(mat)
    await db_session.flush()
    mat_id = mat.id

    response = await client.post(
        "/api/v1/admin/dishes",
        json={
            "name": "测试菜品",
            "price": 25.00,
            "description": "测试描述",
            "material_ids": [mat_id],
        },
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == "测试菜品"
    assert data["data"]["price"] == 25.00
    assert len(data["data"]["materials"]) == 1


@pytest.mark.anyio
async def test_admin_list_all_dishes(client: AsyncClient, admin_headers: dict) -> None:
    """Test admin listing all dishes."""
    response = await client.get("/api/v1/admin/dishes", headers=admin_headers)
    assert response.status_code == 200


@pytest.mark.anyio
async def test_admin_require_admin(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test that non-admin users cannot access admin endpoints."""
    user = User(openid="normal_user", nickname="普通用户")
    db_session.add(user)
    await db_session.flush()

    token = create_access_token(subject=str(user.id), role="user")
    response = await client.post(
        "/api/v1/admin/categories",
        json={"name": "test", "sort_order": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_admin_review_pending_dish(client: AsyncClient, admin_headers: dict, db_session: AsyncSession) -> None:
    """Test admin reviewing a pending dish."""
    user = User(openid="test_user", nickname="测试用户")
    db_session.add(user)
    await db_session.flush()

    from src.models.pending_dish import PendingDish
    pending = PendingDish(user_id=user.id, name="用户自定义菜")
    db_session.add(pending)
    await db_session.flush()

    response = await client.post(
        f"/api/v1/admin/pending-dishes/{pending.id}/review",
        json={
            "status": "approved",
            "admin_price": 42.00,
            "admin_note": "已审核，价格合理",
        },
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "approved"
    assert data["data"]["admin_price"] == 42.00
