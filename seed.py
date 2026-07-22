"""初始化用户数据（首次部署后执行一次）

用法：
    python seed.py

或在 Railway Shell 中运行：
    alembic upgrade head
    python seed.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.models.user import User
from src.core.config import settings
from src.core.security import hash_password


USERS = [
    {"username": "admin", "password": "adsl305088202", "nickname": "管理员", "role": "admin"},
    {"username": "dcyzxz", "password": "adsl305088202", "nickname": "厨师长", "role": "chef"},
    {"username": "wosnx", "password": "www.adsl305088202.com", "nickname": "点菜用户", "role": "user"},
]


async def seed():
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession)

    async with async_session() as db:
        for u in USERS:
            result = await db.execute(select(User).where(User.username == u["username"]))
            existing = result.scalar_one_or_none()
            if existing:
                print(f"  ⏭️  {u['username']} 已存在，跳过")
                continue

            user = User(
                username=u["username"],
                password_hash=hash_password(u["password"]),
                nickname=u["nickname"],
                role=u["role"],
            )
            db.add(user)
            print(f"  ✅ 创建 {u['role']}: {u['username']}")

        await db.commit()

    await engine.dispose()
    print("\n🎉 用户初始化完成！")


if __name__ == "__main__":
    print("正在初始化用户...")
    asyncio.run(seed())
