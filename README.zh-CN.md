# 多用户家庭账单管理系统（my-bill-2）

**[English](./README.md)** | 中文

基于 **React + TypeScript + Vite** 与 **FastAPI + PostgreSQL** 的家庭账单管理系统：多用户与家庭协作、账单导入与解析、分类与统计图表、系统消息与可配置分类规则。

## 项目概述

支持从 **支付宝、京东、招商银行、微信支付、美团** 等来源导入账单（CSV / Excel / PDF 等），在仪表盘中查看收支趋势与分类占比，并可通过 **分类规则**（含可选智谱 AI 辅助）将交易归入账单分类。

### 核心特性

- **多用户与家庭**：注册登录、JWT、家庭创建与成员管理、家庭内共享数据视角
- **账单解析**：`backend/parsers/` 中按 `source_type` 注册解析器（支付宝、京东、招行、微信、美团等）
- **账单与分类**：账单 CRUD、分类树、上传预览与确认、可选重复检测与覆盖逻辑（见代码与迁移脚本）
- **统计与图表**：仪表盘、年度支出、月度趋势、分类占比等（Recharts / ECharts）
- **分类规则**：自定义规则，支持 `personal` / `family` 作用域（`/api/v1/classification-rules`）
- **账单代管授权**：家庭成员可授权他人代录/改/删账单（`/api/v1/bill-delegations`）
- **审计日志**：记录账单增删改及代管操作元数据（`/api/v1/audit-logs`）
- **MCP**：13 个 Agent 工具，端点 `/mcp`（REST 管理 `/api/v1/mcp/*`）
- **消息**：家庭/系统消息相关接口与前端页面
- **运维**：健康检查与指标（`/api/v1/health`）、结构化日志、可选 Redis、生产环境关闭 Swagger

## 技术栈

| 层级 | 选型 |
|------|------|
| 前端 | React 18、TypeScript、Vite 7、Ant Design 5、Zustand、React Router 7、Axios、Recharts、ECharts（echarts-for-react） |
| 后端 | Python 3、FastAPI、SQLAlchemy 2.x、Pydantic v2 / pydantic-settings、Uvicorn |
| 认证 | JWT（python-jose）、密码 **bcrypt**（passlib） |
| 数据 | PostgreSQL（`psycopg2-binary` / `asyncpg`），迁移见 `backend/migrations/` |
| 可选 | 智谱 AI（`ZHIPU_API_KEY`，用于智能分类）、Redis（`REDIS_URL`） |

## 仓库结构

```text
my-bill-2/
├── backend/                 # FastAPI 应用（工作目录常为 backend/）
│   ├── api/                 # 路由：auth、bills、upload、families、users、messages、system_config、classification_rules、health、mcp、audit-logs、bill-delegations
│   ├── bill_mcp/            # MCP 工具服务
│   ├── config/              # settings、database、logging；environments/*.env 示例
│   ├── core/                # 中间件、异常
│   ├── models/              # SQLAlchemy 模型
│   ├── schemas/             # Pydantic 模型
│   ├── services/            # 业务服务
│   ├── parsers/             # 各平台账单解析器
│   ├── migrations/          # SQL/Python 迁移脚本
│   ├── main.py              # FastAPI 入口
│   ├── run.py               # 备用 uvicorn 启动
│   ├── create_tables.py     # 核心表（make db-init）；其余表见 backend/migrations/*.sql
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/             # client、config（API 基址与端点）、services
│   │   ├── components/      # 布局、图表等
│   │   ├── pages/           # 登录注册、仪表盘、账单、上传、家庭、消息、用户、分类规则、设置等
│   │   ├── stores/          # Zustand
│   │   └── types/
│   └── package.json
├── database/
│   └── init.sql             # 参考 SQL（以实际迁移与模型为准）
├── docs/                    # 项目梳理、功能说明等
├── scripts/                 # 分析、排错、工具脚本
├── .env.example             # 环境变量模板（复制到 backend/.env，见下）
├── Makefile                 # install、dev-backend、dev-frontend、test、db-init 等
├── pytest.ini               # 预留 pytest 配置（测试用例目录可自行添加 tests/）
├── README.md                # 英文 README（GitHub 默认）
└── README.zh-CN.md          # 中文 README
```

## 环境要求

- **Node.js** 18+
- **Python** 3.9+（与 `backend/requirements.txt` 一致即可）
- **PostgreSQL** 12+

## 快速开始（推荐 Makefile）

```bash
git clone <repository-url>
cd my-bill-2

# 配置环境变量：仓库根目录的示例复制到 backend/.env（后端 BASE_DIR 为 backend/）
cp .env.example backend/.env
# 编辑 backend/.env：至少设置 DATABASE_URL、SECRET_KEY（≥32 字符）

# 安装依赖
make install

# 初始化核心数据库表（在 backend 下执行 create_tables.py）
make db-init
# 按需执行增量迁移，例如：
# psql $DATABASE_URL -f backend/migrations/add_audit_logs.sql

# 分别开两个终端（`make dev` 仅打印地址；实际启动用 dev-backend / dev-frontend）
make dev-backend    # http://127.0.0.1:8000（python main.py）
make dev-frontend   # http://localhost:5173
```

常用命令：`make help`、`make test`（需存在 `tests/` 与用例）、`make lint`、`make format`、`make build`。

### 环境变量说明（要点）

- 配置文件加载顺序见 `backend/config/settings.py`：**优先 `backend/.env`**，否则 `backend/config/environments/{ENVIRONMENT}.env`。
- **SECRET_KEY**：至少 32 字符。
- **CORS_ORIGINS**：逗号分隔，默认包含 `localhost:5173` 等。
- **ALLOWED_EXTENSIONS**：与 `settings` 一致时可包含 `.csv,.xlsx,.xls,.pdf` 等。
- **ZHIPU_API_KEY**：可选，用于 AI 分类相关能力。
- **ACCESS_TOKEN_EXPIRE_MINUTES**：`settings.py` 默认 **240** 分钟；生产环境配置常为 30。
- 根目录 `.env.example` 与后端字段对应；以 `settings.py` 中 `Field` 为准。

### 前端 API 地址

- 开发默认请求 `http://localhost:8000`（见 `frontend/src/api/config.ts`）。
- 生产构建部署在非 localhost 域名时，自动使用 `window.location.origin`。
- 若需强制指向生产 API，使用环境变量 **`VITE_USE_PROD_API=true`**（详见 `getApiBaseUrl()`）。

## 主要路由（前端）

| 路径 | 说明 |
|------|------|
| `/login`、`/register` | 登录注册 |
| `/dashboard`、`/family-dashboard` | 仪表盘（统计与图表） |
| `/bills` | 账单列表与管理 |
| `/upload` | 上传与导入 |
| `/messages` | 消息 |
| `/users` | 用户管理（权限依角色） |
| `/family` | 家庭管理 |
| `/classification-rules` | 分类规则 |
| `/audit-logs` | 审计日志 |
| `/settings` | 设置 |
| `/profile` | 个人中心（含 MCP、账单授权 Tab） |
| `/mcp-settings` | 重定向至 `/profile?tab=mcp` |

## 后端 API 与文档

- 开发环境 Swagger：**http://localhost:8000/docs**。生产环境可能关闭文档访问，以 `ENVIRONMENT` 等配置为准。
- 路由统一前缀：**`/api/v1`**。
- 示例：
  - `POST /api/v1/auth/register`、`POST /api/v1/auth/login`、`GET /api/v1/auth/me`
  - `GET|POST /api/v1/bills`、`GET /api/v1/bills/stats`、财务汇总与图表相关子路径
  - `POST /api/v1/upload`（直接导入）、`GET /api/v1/upload/history`
  - `GET /api/v1/audit-logs`、`GET|POST /api/v1/bill-delegations`
  - `GET /api/v1/mcp/settings`、`GET /api/v1/mcp/info`
  - `GET /api/v1/health/...` 健康检查
- MCP Agent 端点：**`/mcp`**（13 个工具，详见 `docs/project_overview.md`）

完整列表以 OpenAPI 为准。

## 数据模型（概要）

核心实体：`User`、`Family`、`FamilyMember`、`Bill`、`BillCategory`、`Message`、`MessageAction`、`SystemConfig`、`ClassificationRule`、`McpApiKey`、`AuditLog`、`BillDelegation`。关系与字段以 `backend/models/` 为准。

## 安全说明

- **密码**：使用 **bcrypt** 哈希存储，非明文、非 SHA256。
- **Token**：JWT；中间件含 Token 刷新与限流等（见 `backend/core/middleware.py`）。
- **生产**：强 `SECRET_KEY`、HTTPS、收紧 CORS、按需关闭 Swagger。

## 部署与更多文档

- 后端：`backend/DEPLOY.md`、`backend/deploy.sh`
- 前端：`frontend/DEPLOY.md`、`frontend/deploy.sh`
- PostgreSQL：`POSTGRES_SETUP.md`
- 架构梳理：`docs/project_overview.md`
- 年度支出图表等专题：`docs/年度支出图表模块实现说明书.md`
- 账单分类体系：`账单分类体系.md`
- 分类规则脚本：`backend/scripts/README_classification_rules.md`

## 故障排除

- **数据库连接失败**：检查 PostgreSQL 服务、`DATABASE_URL`、防火墙与数据库用户权限。
- **CORS**：将前端源加入 `CORS_ORIGINS`。
- **上传失败**：检查 `ALLOWED_EXTENSIONS`、`MAX_FILE_SIZE`、`backend/uploads` 目录权限及解析器是否支持该 `source_type`。

---

维护文档时请同步更新 `docs/project_overview.md` 与本 README，并与 `backend/config/settings.py`、路由注册保持一致。
