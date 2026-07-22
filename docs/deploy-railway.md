# Railway 部署指南

## 步骤

### 1. 推送代码到 GitHub

```bash
git init
git add .
git commit -m "init: 点菜小程序"
git remote add origin https://github.com/你的用户名/order.git
git push -u origin main
```

### 2. 在 Railway 创建项目

1. 打开 [Railway](https://railway.app) 并登录（用 GitHub 账号）
2. 点 **New Project** → **Deploy from GitHub repo**
3. 选择刚推送的仓库
4. Railway 会自动识别 Python 项目并开始构建

### 3. 添加 MySQL

1. 在项目页面点 **New** → **Database** → **MySQL**
2. 等待 MySQL 创建完成
3. 点 MySQL 服务 → **Connect** → 复制连接信息
4. 将 `DATABASE_URL` 和 `DATABASE_URL_SYNC` 格式改为：
   ```
   DATABASE_URL=mysql+asyncmy://用户名:密码@主机:3306/数据库名?charset=utf8mb4
   DATABASE_URL_SYNC=mysql+pymysql://用户名:密码@主机:3306/数据库名?charset=utf8mb4
   ```

### 4. 设置环境变量

在 Railway dashboard 中设置：

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | 异步 MySQL 连接串 |
| `DATABASE_URL_SYNC` | 同步 MySQL 连接串 |
| `JWT_SECRET_KEY` | 随机字符串（生成: `openssl rand -hex 32`） |
| `JWT_EXPIRATION_HOURS` | `72` |
| `DEBUG` | `false` |
| `ADMIN_USERNAME` | `admin` |
| `ADMIN_PASSWORD` | 你自己设的管理员密码 |

### 5. 数据库迁移

部署成功后，在 Railway 的 **Shell** 标签页执行：

```bash
alembic upgrade head
```

### 6. 访问

部署完成后 Railway 会分配一个 `.railway.app` 域名，直接用浏览器打开即可。

## 本地调试

```bash
# 安装依赖
pip install -r requirements.txt

# 启动
uvicorn main:app --reload --port 8000

# 浏览器访问
open http://localhost:8000
```
