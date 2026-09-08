# 专综2 项目

Vue3 + FastAPI + MySQL 全栈项目，当前已实现**用户注册 / 登录**（JWT 认证）。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3 + Vite + Vue Router + Element Plus + Axios |
| 后端 | FastAPI + SQLAlchemy + PyMySQL + PyJWT + passlib(bcrypt) |
| 数据库 | MySQL 8.x |

## 目录结构

```
专综2/
├── backend/               # FastAPI 后端
│   ├── app/
│   │   ├── main.py        # 应用入口，CORS、路由注册
│   │   ├── config.py      # 数据库/JWT 配置（读 .env）
│   │   ├── database.py    # SQLAlchemy 引擎与会话
│   │   ├── models.py      # ORM 模型（users 表）
│   │   ├── schemas.py     # Pydantic 请求/响应模型
│   │   ├── security.py    # bcrypt 密码哈希 + JWT 签发/校验
│   │   ├── deps.py        # 依赖：解析当前登录用户
│   │   └── routers/
│   │       └── auth.py    # 注册/登录/获取当前用户
│   ├── init.sql           # 建库脚本
│   ├── requirements.txt
│   └── .env.example       # 环境变量模板
└── frontend/              # Vue3 前端
    ├── src/
    │   ├── api/           # axios 封装 + 认证接口
    │   ├── router/        # 路由 + 登录守卫
    │   └── views/         # LoginView / RegisterView / HomeView
    ├── vite.config.js     # /api 代理到 8000 端口
    └── package.json
```

## 快速启动

### 1. 准备数据库

```sql
CREATE DATABASE IF NOT EXISTS zhuanzong2
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
```

> 也可以直接执行 `backend/init.sql`。表会在后端首次启动时自动创建。

### 2. 启动后端（端口 8000）

```bash
cd backend

# 建议使用虚拟环境
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# 配置数据库连接（首次）
copy .env.example .env         # 按需修改 DB_PASSWORD 等

uvicorn app.main:app --reload --port 8000
```

启动后访问接口文档：http://127.0.0.1:8000/docs

### 3. 启动前端（端口 5173）

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173 即可看到登录页。

## 接口一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | /api/auth/register | 注册（用户名 3-50 位，密码至少 6 位） |
| POST | /api/auth/login | 登录，返回 JWT 和用户信息 |
| GET | /api/auth/me | 获取当前登录用户（需 Bearer Token） |
| GET | /api/health | 健康检查 |

## 认证流程

1. 注册：前端表单校验 → 后端校验用户名唯一 → bcrypt 哈希后入库
2. 登录：校验密码 → 签发 24 小时有效的 JWT
3. 前端把 Token 存 localStorage，axios 拦截器自动加 `Authorization: Bearer <token>`
4. 路由守卫：无 Token 访问业务页面自动跳转登录页；后端返回 401 时自动登出

## 下一步可扩展

- 密码找回 / 邮箱验证
- 用户管理页面（CRUD）
- 使用 Alembic 做数据库迁移
- Pinia 状态管理
