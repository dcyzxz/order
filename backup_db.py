"""数据库备份脚本 - 在 Railway Shell 执行: python backup_db.py"""
import asyncio
import json
import os
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.core.config import settings
from src.models import *  # noqa
from src.core.database import Base


async def backup():
    engine = create_async_engine(settings.database_url)
    session = async_sessionmaker(engine, class_=AsyncSession)()

    backup_data = {"version": "1.0", "created_at": datetime.now().isoformat(), "tables": {}}

    # Get all table names from metadata
    for table_name, table in Base.metadata.tables.items():
        try:
            result = await session.execute(select(table))
            rows = [dict(row._mapping) for row in result.all()]
            # Convert non-serializable types
            for row in rows:
                for k, v in row.items():
                    if hasattr(v, "isoformat"):
                        row[k] = v.isoformat()
                    elif hasattr(v, "hex"):
                        row[k] = str(v)
            backup_data["tables"][table_name] = rows
            print(f"  ✅ {table_name}: {len(rows)} 条记录")
        except Exception as e:
            print(f"  ⚠️ {table_name}: 读取失败 - {e}")

    await session.close()
    await engine.dispose()

    # Save to file
    filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n🎉 备份完成！文件: {filename}")
    print(f"📦 大小: {os.path.getsize(filename) / 1024:.1f} KB")
    print(f"\n💡 在 Shell 执行 cat {filename} 查看内容")
    print(f"💡 或执行以下命令下载到本地（在新终端执行）：")
    print(f"   curl -o {filename} https://web-production-29a33.up.railway.app/static/{filename}")
    print(f"\n⚠️ 注意：备份文件包含所有数据，请妥善保管！")


if __name__ == "__main__":
    print("🔄 正在备份数据库...\n")
    asyncio.run(backup())
