# 点菜小程序 (Order Mini-App)

一个面向餐饮场景的点菜系统，包含用户点餐端和管理员管理端。支持 **Web 端** 和 **微信小程序** 两种前端。

## 功能特性

### 用户端
- **浏览菜单**：查看全部菜品及每道菜的材料清单
- **忌口排除**：下单时通过勾选排除不想要的食材
- **待定价菜品**：提交当前菜单中没有的菜，由管理员审核定价
- **购物车**：菜品加入购物车，统一提交订单
- **订单管理**：查看订单状态、取消待处理订单

### 管理端
- **菜品管理**：上架、下架、编辑菜品信息
- **材料管理**：管理食材清单，标记过敏原
- **分类管理**：菜品分类排序
- **订单管理**：查看、确认、完成订单
- **定价审核**：审核用户提交的待定价菜品

## 技术栈

- **后端框架**: FastAPI (Python 3.11+)
- **数据库**: MySQL 8.0 + SQLAlchemy (async)
- **缓存**: Redis
- **数据校验**: Pydantic v2
- **数据库迁移**: Alembic
- **前端**: Web (移动端适配 SPA) / 微信小程序
- **测试**: pytest + httpx
- **容器化**: Docker + docker-compose

## 部署方式

### 方式一：Railway 一键部署（推荐）

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template)

详见 [部署文档](docs/deploy-railway.md)

### 方式二：Docker Compose

```bash
docker-compose up -d
# 访问 http://localhost:8000
```

### 方式三：手动启动

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8000
```

### 访问

- **Web 前端**：http://localhost:8000
- **API 文档**：http://localhost:8000/docs

## 项目结构

```
├── src/
│   ├── api/          # 接口层 (路由、依赖注入)
│   │   └── v1/       # API v1 版本
│   ├── services/     # 业务服务层
│   ├── models/       # SQLAlchemy ORM 模型
│   ├── schemas/      # Pydantic 校验模型
│   ├── core/         # 核心配置、异常、安全
│   ├── tasks/        # 异步任务
│   └── generated/    # 自动生成代码 (勿修改)
├── migrations/       # Alembic 迁移脚本
├── tests/            # 测试
├── miniapp/          # 小程序前端
├── main.py           # 应用入口
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## 开发命令

```bash
# 启动开发服务器
uvicorn main:app --reload

# 运行测试
pytest

# 运行特定测试
pytest tests/test_orders.py

# 代码检查
ruff check .
ruff format .

# 类型检查
mypy .

# 数据库迁移
alembic upgrade head
alembic revision --autogenerate -m "description"
```

## API 概览

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | /api/v1/users/login | 微信登录 | 公开 |
| GET  | /api/v1/users/me | 获取用户信息 | 用户 |
| GET  | /api/v1/menu/categories | 菜品分类 | 公开 |
| GET  | /api/v1/menu/dishes | 菜品列表 | 公开 |
| GET  | /api/v1/menu/dishes/{id} | 菜品详情 | 公开 |
| GET  | /api/v1/menu/materials | 材料清单 | 公开 |
| POST | /api/v1/menu/pending-dishes | 提交待定价菜品 | 用户 |
| POST | /api/v1/orders | 创建订单 | 用户 |
| GET  | /api/v1/orders | 订单列表 | 用户 |
| POST | /api/v1/admin/dishes | 创建菜品 | 管理员 |
| POST | /api/v1/admin/pending-dishes/{id}/review | 审核定价 | 管理员 |
| PUT  | /api/v1/admin/orders/{id}/status | 更新订单状态 | 管理员 |

## 数据模型

- **User** - 用户 (微信openid, 昵称, 头像)
- **Category** - 菜品分类
- **Dish** - 菜品 (名称, 描述, 价格, 状态)
- **Material** - 食材材料
- **DishMaterial** - 菜品-材料关联
- **Order** - 订单 (编号, 状态, 总价)
- **OrderItem** - 订单明细 (菜品, 数量, 排除材料)
- **PendingDish** - 待定价菜品 (用户提交, 管理员审核)
