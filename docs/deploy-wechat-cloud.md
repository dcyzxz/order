# 微信云托管部署指南

## 概述

本项目后端部署在 **微信云托管 (WeChat Cloud Hosting)**，小程序前端通过 `wx.cloud.callContainer()` 调用后端 API。

## 部署步骤

### 1. 微信云托管控制台配置

1. 打开 [微信云托管控制台](https://console.cloud.tencent.com/cloudbaserun)
2. 创建/选择环境（当前环境 ID: `prod-d8gcr6ggy9cd4d16c`）
3. 创建服务（服务名: `django-sehm`，即 `SERVICE_NAME`）

### 2. 构建与上传镜像

```bash
# 本地构建镜像
docker build -t ccr.ccs.tencentyun.com/<环境ID>/<服务名>:latest .

# 登录腾讯云容器仓库
docker login ccr.ccs.tencentyun.com --username=<账号ID> --password=<密钥>

# 推送镜像
docker push ccr.ccs.tencentyun.com/<环境ID>/<服务名>:latest
```

或在微信云托管控制台直接上传代码包/关联代码仓库自动构建。

### 3. 环境变量配置

在云托管服务「部署」页面设置以下环境变量：

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `PORT` | 服务端口，云托管自动注入 | `80` |
| `DATABASE_URL` | 数据库连接串 | `mysql+asyncmy://user:pass@host:3306/db?charset=utf8mb4` |
| `DATABASE_URL_SYNC` | 同步数据库连接 | `mysql+pymysql://user:pass@host:3306/db?charset=utf8mb4` |
| `REDIS_URL` | Redis 连接 | `redis://host:6379/0` |
| `JWT_SECRET_KEY` | JWT 签名密钥 | 生产环境使用强随机字符串 |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `DEBUG` | 调试模式 | `false` |

### 4. 数据库说明

项目使用 **MySQL 8.0**（适配微信云托管原生云数据库 MySQL）。

在云托管控制台创建云数据库 MySQL 实例后，将连接信息填入环境变量：

| 变量名 | 示例 |
|--------|------|
| `DATABASE_URL` | `mysql+asyncmy://root:password@host:3306/order_miniapp?charset=utf8mb4` |
| `DATABASE_URL_SYNC` | `mysql+pymysql://root:password@host:3306/order_miniapp?charset=utf8mb4` |

> **注意**：MySQL 连接串必须包含 `?charset=utf8mb4`，确保支持中文和 emoji。

### 5. 前端配置

`miniapp/utils/api.js` 中已配置：

```javascript
const CLOUD_ENV = 'prod-d8gcr6ggy9cd4d16c'     // 云环境ID
const SERVICE_NAME = 'django-sehm'              // 云托管服务名
```

### 6. 健康检查

云托管要求容器提供健康检查端点。项目已内置 `/health` 端点：

```json
GET /health → {"status": "healthy"}
```

## 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 访问 API 文档
http://localhost:8000/docs
```
