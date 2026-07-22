"""初始化常见食材数据
用法: 在 Railway Shell 执行 python seed_materials.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.models.material import Material
from src.core.config import settings

MATERIALS = [
    # ===== 肉类 =====
    ("猪肉", "肉类", False),
    ("五花肉", "肉类", False),
    ("瘦肉", "肉类", False),
    ("排骨", "肉类", False),
    ("猪肝", "肉类", False),
    ("猪肚", "肉类", False),
    ("猪蹄", "肉类", False),
    ("猪大肠", "肉类", False),
    ("里脊肉", "肉类", False),
    ("牛肉", "肉类", False),
    ("牛腩", "肉类", False),
    ("牛腱子", "肉类", False),
    ("牛百叶", "肉类", False),
    ("羊肉", "肉类", False),
    ("羊排", "肉类", False),
    ("鸡", "肉类", False),
    ("鸡腿", "肉类", False),
    ("鸡翅", "肉类", False),
    ("鸡胸肉", "肉类", False),
    ("鸡爪", "肉类", False),
    ("鸡胗", "肉类", False),
    ("鸭", "肉类", False),
    ("鸭血", "肉类", False),
    ("鸭肠", "肉类", False),
    ("鸭掌", "肉类", False),
    ("腊肉", "肉类", False),
    ("火腿", "肉类", False),
    ("培根", "肉类", False),
    ("香肠", "肉类", False),

    # ===== 海鲜 =====
    ("虾", "海鲜", True),
    ("虾仁", "海鲜", True),
    ("龙虾", "海鲜", True),
    ("螃蟹", "海鲜", True),
    ("蟹肉棒", "海鲜", True),
    ("鱼", "海鲜", True),
    ("草鱼", "海鲜", True),
    ("鲈鱼", "海鲜", True),
    ("鲫鱼", "海鲜", True),
    ("带鱼", "海鲜", True),
    ("三文鱼", "海鲜", True),
    ("鱿鱼", "海鲜", True),
    ("墨鱼", "海鲜", True),
    ("鲍鱼", "海鲜", True),
    ("扇贝", "海鲜", True),
    ("蛤蜊", "海鲜", True),
    ("花甲", "海鲜", True),
    ("蛏子", "海鲜", True),
    ("海参", "海鲜", True),
    ("鱼丸", "海鲜", True),
    ("鱼片", "海鲜", True),

    # ===== 蔬菜 =====
    ("白菜", "蔬菜", False),
    ("小白菜", "蔬菜", False),
    ("娃娃菜", "蔬菜", False),
    ("菠菜", "蔬菜", False),
    ("油菜", "蔬菜", False),
    ("生菜", "蔬菜", False),
    ("空心菜", "蔬菜", False),
    ("油麦菜", "蔬菜", False),
    ("西兰花", "蔬菜", False),
    ("菜花", "蔬菜", False),
    ("芹菜", "蔬菜", False),
    ("韭菜", "蔬菜", False),
    ("蒜苗", "蔬菜", False),
    ("香菜", "蔬菜", False),
    ("茼蒿", "蔬菜", False),
    ("豆芽", "蔬菜", False),
    ("绿豆芽", "蔬菜", False),
    ("黄豆芽", "蔬菜", False),
    ("土豆", "蔬菜", False),
    ("红薯", "蔬菜", False),
    ("山药", "蔬菜", False),
    ("芋头", "蔬菜", False),
    ("萝卜", "蔬菜", False),
    ("白萝卜", "蔬菜", False),
    ("胡萝卜", "蔬菜", False),
    ("莲藕", "蔬菜", False),
    ("竹笋", "蔬菜", False),
    ("芦笋", "蔬菜", False),
    ("玉米", "蔬菜", False),
    ("豌豆", "蔬菜", False),
    ("四季豆", "蔬菜", False),
    ("豇豆", "蔬菜", False),
    ("毛豆", "蔬菜", False),
    ("茄子", "蔬菜", False),
    ("西红柿", "蔬菜", False),
    ("黄瓜", "蔬菜", False),
    ("冬瓜", "蔬菜", False),
    ("南瓜", "蔬菜", False),
    ("苦瓜", "蔬菜", False),
    ("丝瓜", "蔬菜", False),
    ("青椒", "蔬菜", False),
    ("红椒", "蔬菜", False),
    ("尖椒", "蔬菜", False),
    ("洋葱", "蔬菜", False),
    ("大蒜", "蔬菜", False),
    ("生姜", "蔬菜", False),
    ("大葱", "蔬菜", False),
    ("小葱", "蔬菜", False),
    ("蘑菇", "蔬菜", False),
    ("香菇", "蔬菜", False),
    ("金针菇", "蔬菜", False),
    ("杏鲍菇", "蔬菜", False),
    ("木耳", "蔬菜", False),
    ("银耳", "蔬菜", False),
    ("海带", "蔬菜", False),
    ("紫菜", "蔬菜", False),

    # ===== 豆制品/蛋 =====
    ("豆腐", "豆制品", False),
    ("嫩豆腐", "豆制品", False),
    ("老豆腐", "豆制品", False),
    ("豆腐干", "豆制品", False),
    ("千张", "豆制品", False),
    ("腐竹", "豆制品", False),
    ("豆腐皮", "豆制品", False),
    ("豆泡", "豆制品", False),
    ("鸡蛋", "豆制品", False),
    ("鸭蛋", "豆制品", False),
    ("皮蛋", "豆制品", False),
    ("咸鸭蛋", "豆制品", False),
    ("鹌鹑蛋", "豆制品", False),
    ("豆浆", "豆制品", True),

    # ===== 主食/粉面 =====
    ("米饭", "主食", False),
    ("面条", "主食", False),
    ("米粉", "主食", False),
    ("河粉", "主食", False),
    ("粉丝", "主食", False),
    ("年糕", "主食", False),
    ("饺子皮", "主食", False),
    ("馄饨皮", "主食", False),
    ("馒头", "主食", False),
    ("花卷", "主食", False),
    ("油条", "主食", False),
    ("面包", "主食", False),
    ("糯米", "主食", False),
    ("小米", "主食", False),

    # ===== 调料 =====
    ("盐", "调料", False),
    ("糖", "调料", False),
    ("生抽", "调料", False),
    ("老抽", "调料", False),
    ("醋", "调料", False),
    ("料酒", "调料", False),
    ("耗油", "调料", False),
    ("味精", "调料", False),
    ("鸡精", "调料", False),
    ("胡椒粉", "调料", False),
    ("花椒", "调料", True),
    ("麻椒", "调料", True),
    ("干辣椒", "调料", False),
    ("辣椒粉", "调料", False),
    ("豆瓣酱", "调料", False),
    ("甜面酱", "调料", False),
    ("番茄酱", "调料", False),
    ("芝麻酱", "调料", True),
    ("花生酱", "调料", True),
    ("辣椒酱", "调料", False),
    ("蒜蓉", "调料", False),
    ("姜末", "调料", False),
    ("葱段", "调料", False),
    ("八角", "调料", False),
    ("桂皮", "调料", False),
    ("香叶", "调料", False),
    ("孜然", "调料", False),
    ("芝麻", "调料", True),
    ("香油", "调料", False),
    ("辣椒油", "调料", False),
    ("花椒油", "调料", False),
    ("食用油", "调料", False),
    ("淀粉", "调料", False),
    ("小苏打", "调料", False),
    ("泡打粉", "调料", False),
    ("酵母", "调料", False),

    # ===== 水果 =====
    ("柠檬", "水果", True),
    ("橙子", "水果", True),
    ("苹果", "水果", True),
    ("香蕉", "水果", True),
    ("菠萝", "水果", True),
    ("芒果", "水果", True),
    ("椰子", "水果", True),
    ("荔枝", "水果", True),
    ("龙眼", "水果", True),
    ("草莓", "水果", True),
    ("蓝莓", "水果", True),
    ("西瓜", "水果", False),
    ("哈密瓜", "水果", False),
    ("葡萄干", "水果", False),
    ("红枣", "水果", False),
    ("枸杞", "水果", False),

    # ===== 干货/其他 =====
    ("花生", "其他", True),
    ("核桃", "其他", True),
    ("腰果", "其他", True),
    ("杏仁", "其他", True),
    ("松子", "其他", True),
    ("开心果", "其他", True),
    ("瓜子", "其他", True),
    ("白芝麻", "其他", True),
    ("黑芝麻", "其他", True),
    ("葡萄干", "其他", False),
    ("桂圆干", "其他", False),
    ("干贝", "其他", False),
    ("虾米", "其他", True),
    ("干香菇", "其他", False),
    ("黄花菜", "其他", False),
    ("茶树菇", "其他", False),
    ("虫草花", "其他", False),
]


async def seed_materials():
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession)

    async with async_session() as db:
        # Check existing materials count
        result = await db.execute(select(Material))
        existing = result.scalars().all()
        existing_names = {m.name for m in existing}
        count = 0

        for name, category, is_allergen in MATERIALS:
            if name in existing_names:
                continue
            mat = Material(name=name, category=category, is_allergen=is_allergen)
            db.add(mat)
            count += 1
            existing_names.add(name)

        await db.commit()
        print(f"✅ 新增 {count} 种材料 (已有 {len(existing)} 种)")
        print(f"📊 共 {len(existing) + count} 种材料")

    await engine.dispose()


if __name__ == "__main__":
    print("正在初始化食材数据...")
    asyncio.run(seed_materials())
