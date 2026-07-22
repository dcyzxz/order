# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

一个面向餐饮场景的点菜小程序，包含用户点餐端和管理员管理端。用户进入小程序后可查看全部菜品及每道菜的材料清单，下单时可通过勾选排除不想要的材料；若用户点了当前菜单中没有的菜，系统将其记录为"待定价菜品"，由管理员审核并补充定价后正式上架。

## 技术栈

- **语言**: Python
- **后端框架**: FastAPI
- **数据库**: PostgreSQL
- **ORM**: SQLAlchemy
- **数据校验/类型**: Pydantic
- **缓存/消息**: Redis
- **数据库迁移**: Alembic
- **管理后台**: FastAPI 提供后台管理 API，可配合轻量管理前端或模板页面
- **小程序前端**: uni-app / 微信小程序（与后端通过 RESTful API 交互）
- **测试**: pytest
- **其他**: Docker, uv/pip, Ruff, mypy

## 常用命令

- **启动开发服务器**: ***`uvicorn main:app --reload`***
- **安装依赖**: ***`pip install -r requirements.txt`*** 或 ***`uv sync`***
- **运行测试**: ***`pytest`***
- **运行特定测试**: ***`pytest tests/test_orders.py`***
- **代码检查**: ***`ruff check .`*** 和 ***`ruff format .`***
- **类型检查**: ***`mypy .`***
- **数据库迁移**: ***`alembic upgrade head`***

## 开发规范与约定

- **代码风格**: 使用 Ruff 进行代码格式化和检查，提交前必须通过 ***`ruff check .`***。
- **提交信息**: 使用约定式提交 (Conventional Commits)，格式为 ***`<type>(<scope>): <description>`***，例如 ***`feat(menu): add dish material exclusion`***。
- **项目结构**: 按功能模块划分（menu、orders、users、admin 等），避免单个文件超过 300 行。
- **类型安全**: 必须使用 Pydantic 模型进行输入校验和序列化，禁止在函数签名中使用裸 ***`dict`*** 或 ***`Any`***。
- **错误处理**: API 统一返回 ***`{ code, data, message }`*** 格式，业务异常使用自定义 ***`OrderException`*** 进行抛出和捕获。
- **数据校验**: 菜品定价、材料信息、订单备注等关键字段必须在 Pydantic Schema 层严格校验。
- **待定价流程**: 用户提交菜单外菜品时，状态必须为 ***`pending_price`***，管理员补充定价并启用后才可展示在用户端。

## 架构与目录说明

- ***`src/api/`***: 外部接口层，包含小程序端 API、管理后台 API、依赖注入与请求响应模型。
- ***`src/services/`***: 业务领域服务，例如 menu、orders、users、pricing、admin 等。
- ***`src/models/`***: SQLAlchemy 数据库 ORM 模型定义，包括 Dish、Material、Order、OrderItem 等。
- ***`src/schemas/`***: Pydantic 数据校验、序列化和 API 返回模型。
- ***`src/core/`***: 全局配置、日志、依赖注入容器、全局异常处理、认证与权限。
- ***`src/tasks/`***: 异步任务（如订单通知、统计汇总）与调度相关逻辑。
- ***`migrations/`***: Alembic 数据库迁移脚本。
- ***`tests/`***: 单元测试、集成测试和 fixtures。
- ***`miniapp/`***: 小程序前端源码目录（若与后端仓库统一管理）。

## 注意事项

- 不要修改 ***`src/generated/`*** 目录下的任何文件，它们是自动生成的。
- 涉及敏感配置（如数据库密码、Redis 密码、JWT Secret）必须使用环境变量，参考 ***`.env.example`***。
- 在修改数据库 Schema 前，请先与我确认，避免破坏现有订单或菜单数据。
- 管理员定价操作会直接影响用户端菜单展示，必须记录变更日志。
- 用户选择的忌口/排除材料必须随订单一起持久化，避免厨房按原配方制作。
- 小程序端和后端接口版本需保持一致，接口变更时同步更新小程序调用逻辑。
