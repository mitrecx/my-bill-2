# 项目梳理文档

> **最后更新**: 2026-05-31  
> **仓库名**: `my-bill-2`

---

## 目录

1. [项目概述](#项目概述)
2. [技术栈](#技术栈)
3. [整体目录结构](#整体目录结构)
4. [后端架构](#后端架构)
5. [API 概览](#api-概览)
6. [MCP 集成](#mcp-集成)
7. [数据库模型与关系](#数据库模型与关系)
8. [前端架构与路由](#前端架构与路由)
9. [账单解析器](#账单解析器)
10. [测试与质量](#测试与质量)
11. [配置与环境变量](#配置与环境变量)
12. [部署与运维](#部署与运维)
13. [相关文档索引](#相关文档索引)

---

## 项目概述

本项目是 **个人/家庭账单管理系统**：账单导入、多来源解析、分类与规则（含可选智谱 AI）、家庭协作、账单代管授权、审计日志、MCP 对外接口、消息、统计图表与系统配置。前后端分离，REST API 前缀 **`/api/v1`**；MCP Streamable HTTP 端点为 **`/mcp`**（见 `backend/main.py`）。

---

## 技术栈

### 后端

| 领域 | 选型 | 说明 |
|------|------|------|
| Web | FastAPI | 路由、依赖注入、OpenAPI |
| ORM | SQLAlchemy 2.x | 模型与查询 |
| 校验 / 配置 | Pydantic v2、pydantic-settings | `Settings`、请求响应模型 |
| 数据库 | PostgreSQL | 连接串 `DATABASE_URL` |
| 安全 | python-jose、passlib bcrypt | JWT、密码哈希（**非 SHA256**） |
| 解析 | pandas、openpyxl、PyMuPDF 等 | CSV/Excel/PDF 按解析器而定 |
| MCP | FastMCP | `backend/bill_mcp/server.py`，经 `/mcp` 暴露 |

### 前端

| 领域 | 选型 | 说明 |
|------|------|------|
| UI | React 18 + TypeScript + Vite 7 | 与 `frontend/package.json` 一致 |
| 组件 | Ant Design 5 | |
| 路由 | React Router 7 | `App.tsx` 中声明式路由 |
| 状态 | Zustand | `stores/*` |
| 请求 | Axios | `api/client.ts` 拦截器、`api/services.ts` 封装 |
| 图表 | Recharts、ECharts | 仪表盘与专项图表组件 |

---

## 整体目录结构

```text
my-bill-2/
├── backend/
│   ├── api/              # 各模块路由，汇总于 api/__init__.py → api_router
│   ├── bill_mcp/         # MCP 工具服务（Family Bills MCP）
│   ├── config/           # settings、database、logging；config/environments/*.env
│   ├── core/             # 中间件、异常
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── parsers/          # 各平台解析器 + PARSER_MAP
│   ├── migrations/       # 增量 SQL（审计、MCP、代管授权等）
│   ├── scripts/          # 如分类规则管理
│   ├── main.py           # FastAPI 入口（Makefile dev-backend 使用）
│   ├── run.py            # 备用 uvicorn 启动脚本
│   └── create_tables.py  # 仅创建核心 ORM 表（见下文）
├── frontend/src/
│   ├── api/
│   ├── components/
│   ├── pages/
│   ├── stores/
│   └── types/
├── database/init.sql       # 参考脚本
├── docs/                   # 本文档等
├── scripts/                # 仓库级分析/调试脚本
└── pytest.ini              # pytest 配置（测试目录可自建 tests/）
```

**约定**：路由层只做参数与权限，复杂逻辑在 `services/`；前端页面通过 `api/services.ts` 调用后端。

---

## 后端架构

### 应用入口

- `backend/main.py`：创建 `FastAPI` 实例，注册 CORS、`core` 中间件（安全头、请求日志、Token 刷新、生产环境限流等）、`setup_exception_handlers`，挂载 `api_router`（前缀 `/api/v1`），并注册 MCP 传输（`/mcp`）。
- `lifespan`：初始化日志、创建上传与日志目录。
- 生产环境可通过 `settings.is_production` 关闭 `/docs`、`/redoc`。

### 路由模块（`api/__init__.py`）

| 模块 | 前缀（相对 `/api/v1`） | 说明 |
|------|------------------------|------|
| `auth` | `/auth` | 注册、登录、当前用户 |
| `families` | `/families` | 家庭与成员 |
| `bills` | `/bills` | 账单、统计、分类、图表数据等 |
| `upload` | `/upload` | 上传、历史、统计（`POST /upload` 直接入库） |
| `health` | `/health` | 健康检查与指标 |
| `messages` | `/messages` | 消息列表、`/unread-count`、`/{message_id}`、`/{message_id}/actions` |
| `users` | `/users` | 用户与个人资料 |
| `system_config` | `/system-config` | 系统配置 |
| `classification_rules` | `/classification-rules` | 分类规则 CRUD、批量、选项接口 |
| `mcp_settings` | `/mcp` | MCP API Key 与服务器信息（REST 管理面） |
| `audit` | `/audit-logs` | 账单等数据变更审计 |
| `bill_delegations` | `/bill-delegations` | 家庭成员账单代管授权 |

具体路径以各文件内 `APIRouter` 及 OpenAPI 为准。

### 中间件与异常

- `core/middleware.py`：CORS 在 `main` 中最先注册；含 Token 刷新、请求日志、安全响应头、速率限制等。
- `core/exceptions.py`：统一异常到 JSON。

### 数据层

- `config/database.py`：`SessionLocal`、`get_db`。
- 模型见 `models/__init__.py` 导出：`User`、`Family`、`FamilyMember`、`Bill`、`BillCategory`、`Message`、`MessageAction`、`SystemConfig`、`ClassificationRule`、`McpApiKey`、`AuditLog`、`BillDelegation`。

### 数据库初始化说明

- `create_tables.py` / `make db-init` 仅根据已导入的核心模型建表（`User`、`Family`、`FamilyMember`、`Bill`、`BillCategory`）。
- 消息、分类规则、系统配置、MCP Key、审计日志、账单代管等表需额外执行 `backend/migrations/*.sql`（如 `add_message_system.sql`、`add_audit_logs.sql`、`add_mcp_api_keys.sql`、`add_bill_delegations.sql` 等）。

---

## API 概览

- 完整列表：**开发环境启动后访问 `/docs`**。
- 认证：多数写操作需 Header `Authorization: Bearer <token>`。
- 上传：当前实现为 **`POST /api/v1/upload`**（非独立的 preview/confirm 两步接口）。

---

## MCP 集成

- **传输端点**：`POST/GET /mcp`（Streamable HTTP，`register_mcp_transport` in `main.py`）。
- **认证**：`Authorization: Bearer <MCP_API_KEY>`（在设置页或 `POST /api/v1/mcp/settings/api-key` 生成）。
- **管理 REST**：`GET /api/v1/mcp/settings`、`GET /api/v1/mcp/info` 等。
- **工具（13 个，见 `bill_mcp/server.py`）**：

| 工具名 | 用途 |
|--------|------|
| `query_family_members` | 查询家庭成员及账单操作权限（用于确定 `target_user_id`） |
| `create_bill` / `create_bills_batch` | 录入账单（支持 `target_user_id` 代管录入） |
| `query_bills_batch` | 多条件查询家庭账单 |
| `query_bill_categories` | 查询分类列表 |
| `update_bill` / `update_bills_batch` | 修改账单（含代管授权） |
| `delete_bill` / `delete_bills_batch` | 删除账单（含代管授权） |
| `query_classification_rules` | 查询分类规则 |
| `create_classification_rule` / `update_classification_rule` / `delete_classification_rule` | 分类规则维护 |

---

## 数据库模型与关系（概要）

- **User** 与 **Bill** 一对多；**User** 通过 **FamilyMember** 与 **Family** 多对多。
- **Bill** 关联 **BillCategory**；分类支持逻辑删除等字段（以模型为准）。
- **ClassificationRule**：支持 `personal` / `family` 作用域（见迁移 `add_scope_to_classification_rules.sql`）。
- **Message** / **MessageAction**：消息与操作记录。
- **AuditLog**：账单等实体增删改审计（`meta` 可标记代管操作 `delegated`）。
- **BillDelegation**：授权人对被授权人的账单录入/修改/删除权限。
- **McpApiKey**：MCP 访问密钥（哈希存储）。

详细 ER 若需图示，建议根据当前 `models/*.py` 重新生成。

---

## 前端架构与路由

- **入口**：`main.tsx`、`App.tsx`。
- **鉴权**：`ProtectedRoute` 使用 `useAuthStore` 的 `isAuthenticated`；未登录跳转 `/login`。
- **布局**：`Layout` 作为父级子路由容器。

### 主要页面（`pages/`）

`DashboardPage`、`BillsPage`、`UploadPage`、`MessagesPage`、`UsersManagePage`、`FamilyManagePage`、`ClassificationRulesPage`、`AuditLogsPage`、`SettingsPage`、`PersonalCenterPage`（含 MCP、账单授权 Tab）、`LoginPage`、`RegisterPage`。

### 路由表（`App.tsx`）

| 路径 | 说明 |
|------|------|
| `/dashboard`、`/family-dashboard` | 仪表盘 |
| `/bills` | 账单管理（含代管录入） |
| `/upload` | 上传导入 |
| `/messages` | 消息 |
| `/users` | 用户管理 |
| `/family` | 家庭管理 |
| `/classification-rules` | 分类规则 |
| `/audit-logs` | 审计日志 |
| `/settings` | 系统设置 |
| `/profile` | 个人中心（`?tab=mcp` MCP 设置，`?tab=delegation` 账单授权） |
| `/mcp-settings` | 重定向至 `/profile?tab=mcp` |

统计分析已整合进仪表盘等页面，无独立 `StatsPage`。

### API 基址

- 开发默认 `http://localhost:8000`。
- 生产构建在非 localhost 域名下自动使用 `window.location.origin`；也可用 `VITE_USE_PROD_API=true` 强制生产 API（见 `frontend/src/api/config.ts`）。

---

## 账单解析器

注册表见 `backend/parsers/__init__.py` 中 `PARSER_MAP` / `get_available_parsers()`：

| source_type | 说明 |
|-------------|------|
| alipay | 支付宝 CSV |
| jd | 京东 CSV |
| cmb | 招商银行 PDF |
| wechat | 微信支付 Excel |
| meituan | 美团 CSV |

各解析器继承 `BaseParser`，由上传流程按来源选择。

---

## 测试与质量

- 仓库根目录有 **`pytest.ini`**，约定测试路径为 `tests/`；若目录中尚无用例，`make test` 会跳过并提示。
- **Makefile**：`dev` 仅打印开发地址，实际启动用 `dev-backend` / `dev-frontend`；另有 `lint`、`format`、`db-init` 等（`make help`）。
- 前端无强制单元测试框架配置；可按需引入 Vitest 等。

---

## 配置与环境变量

- **`backend/config/settings.py`**：`Settings` 从环境变量与 `.env` 读取；**优先** `backend/.env`（`BASE_DIR` 为 backend），否则 `config/environments/{ENVIRONMENT}.env`。
- 重要字段：`DATABASE_URL`、`SECRET_KEY`（≥32）、`ALGORITHM`、`ACCESS_TOKEN_EXPIRE_MINUTES`（代码默认 **240** 分钟，生产 env 文件常为 30）、`CORS_ORIGINS`、`UPLOAD_DIR`、`MAX_FILE_SIZE`、`ALLOWED_EXTENSIONS`、`LOG_*`、`REDIS_URL`（可选）、`ZHIPU_API_KEY`（可选）。
- 根目录 **`.env.example`** 可复制为 **`backend/.env`** 后修改。

---

## 部署与运维

- 后端：`backend/DEPLOY.md`、`deploy.sh`；生产路径示例 `/home/josie/apps/family-bills-backend`。
- 前端：`frontend/DEPLOY.md`、静态资源 `npm run build`；生产 **Swagger 默认关闭**（`/docs` 仅开发环境）。
- 有 schema 变更时，在服务器执行 `backend/migrations/` 下对应 SQL。
- SSL 示例：`ssl-certs/`。
- 数据库安装参考：`POSTGRES_SETUP.md`。

---

## 相关文档索引

| 文档 | 内容 |
|------|------|
| [README.md](../README.md) | 快速开始、结构、特性（英文默认） |
| [README.zh-CN.md](../README.zh-CN.md) | 中文版 README |
| [backend/SETUP.md](../backend/SETUP.md) | 后端安装与运行 |
| [backend/DEPLOY.md](../backend/DEPLOY.md) | 后端部署 |
| [frontend/DEPLOY.md](../frontend/DEPLOY.md) | 前端部署 |
| [POSTGRES_SETUP.md](../POSTGRES_SETUP.md) | PostgreSQL |
| [年度支出图表模块实现说明书.md](./年度支出图表模块实现说明书.md) | 年度支出图表 |
| [账单分类体系.md](../账单分类体系.md) | 分类体系 |
| [backend/scripts/README_classification_rules.md](../backend/scripts/README_classification_rules.md) | 分类规则脚本 |

---

> 若实现与本文档不符，请以代码与 OpenAPI 为准，并更新本文件。
