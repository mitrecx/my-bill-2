# 项目梳理文档

> **最后更新**: 2026-04-20  
> **仓库名**: `my-bill-2`

---

## 目录

1. [项目概述](#项目概述)
2. [技术栈](#技术栈)
3. [整体目录结构](#整体目录结构)
4. [后端架构](#后端架构)
5. [API 概览](#api-概览)
6. [数据库模型与关系](#数据库模型与关系)
7. [前端架构与路由](#前端架构与路由)
8. [账单解析器](#账单解析器)
9. [测试与质量](#测试与质量)
10. [配置与环境变量](#配置与环境变量)
11. [部署与运维](#部署与运维)
12. [相关文档索引](#相关文档索引)

---

## 项目概述

本项目是 **个人/家庭账单管理系统**：账单导入、多来源解析、分类与规则（含可选智谱 AI）、家庭协作、消息、统计图表与系统配置。前后端分离，REST API 前缀 **`/api/v1`**。

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
│   ├── config/           # settings、database、logging；config/environments/*.env
│   ├── core/             # 中间件、异常
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── parsers/          # 各平台解析器 + PARSER_MAP
│   ├── migrations/       # 增量 SQL/Python
│   ├── scripts/          # 如分类规则管理
│   ├── main.py
│   ├── run.py
│   └── create_tables.py
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

- `backend/main.py`：创建 `FastAPI` 实例，注册 CORS、`core` 中间件（安全头、请求日志、Token 刷新、生产环境限流等）、`setup_exception_handlers`，挂载 `api_router`（前缀 `/api/v1`）。
- `lifespan`：初始化日志、创建上传与日志目录。
- 生产环境可通过 `settings.is_production` 关闭 `/docs`、`/redoc`。

### 路由模块（`api/__init__.py`）

| 模块 | 前缀（相对 `/api/v1`） | 说明 |
|------|------------------------|------|
| `auth` | `/auth` | 注册、登录、当前用户、刷新 |
| `families` | `/families` | 家庭与成员 |
| `bills` | `/bills` | 账单、统计、分类、图表数据等 |
| `upload` | `/upload` | 预览、确认、历史 |
| `health` | `/health` | 健康检查与指标 |
| `messages` | `/messages` | 消息 |
| `users` | `/users` | 用户管理 |
| `system_config` | `/system-config` | 系统配置 |
| `classification_rules` | `/classification-rules` | 分类规则 CRUD、批量、测试 |

具体路径以各文件内 `APIRouter` 及 OpenAPI 为准。

### 中间件与异常

- `core/middleware.py`：CORS 在 `main` 中最先注册；含 Token 刷新、请求日志、安全响应头、速率限制等。
- `core/exceptions.py`：统一异常到 JSON。

### 数据层

- `config/database.py`：`SessionLocal`、`get_db`。
- 模型见 `models/__init__.py` 导出：`User`、`Family`、`FamilyMember`、`Bill`、`BillCategory`、`Message`、`MessageAction`、`SystemConfig`、`ClassificationRule`。

---

## API 概览

- 完整列表：**启动后访问 `/docs`**（开发环境）。
- 认证：多数写操作需 Header `Authorization: Bearer <token>`。

---

## 数据库模型与关系（概要）

- **User** 与 **Bill** 一对多；**User** 通过 **FamilyMember** 与 **Family** 多对多。
- **Bill** 关联 **BillCategory**；分类支持层级（如 `parent_id`）与逻辑删除等字段（以模型为准）。
- **ClassificationRule**：用户维度规则与来源类型等（见迁移与模型）。
- **Message** / **MessageAction**：消息与操作记录。

详细 ER 若需图示，建议根据当前 `models/*.py` 重新生成，避免与历史 mermaid 不一致。

---

## 前端架构与路由

- **入口**：`main.tsx`、`App.tsx`。
- **鉴权**：`ProtectedRoute` 使用 `useAuthStore` 的 `isAuthenticated`；未登录跳转 `/login`。
- **布局**：`Layout` 作为父级子路由容器。
- **主要页面**（`pages/`）：`DashboardPage`、`BillsPage`、`UploadPage`、`MessagesPage`、`UsersManagePage`、`FamilyManagePage`、`ClassificationRulesPage`、`SettingsPage`、`PersonalCenterPage`、`LoginPage`、`RegisterPage`。
- **统计分析**：独立 `StatsPage` 已移除，汇总类图表在 **仪表盘** 等页面（见各图表组件）。

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

各解析器继承 `BaseParser`，由上传/预览流程按来源选择。

---

## 测试与质量

- 仓库根目录有 **`pytest.ini`**，约定测试路径为 `tests/`；若目录中尚无用例，`make test` 需待补充测试后使用。
- **Makefile**：`lint` 含后端 flake8 与前端 `npm run lint`；`format` 主要为后端 black/isort（前端见 Makefile 说明）。
- 前端无强制单元测试框架配置；可按需引入 Vitest 等。

---

## 配置与环境变量

- **`backend/config/settings.py`**：`Settings` 从环境变量与 `.env` 读取；**优先** `backend/.env`（`BASE_DIR` 为 backend），否则 `config/environments/{ENVIRONMENT}.env`。
- 重要字段：`DATABASE_URL`、`SECRET_KEY`（≥32）、`ALGORITHM`、`ACCESS_TOKEN_EXPIRE_MINUTES`、`CORS_ORIGINS`、`UPLOAD_DIR`、`MAX_FILE_SIZE`、`ALLOWED_EXTENSIONS`、`LOG_*`、`REDIS_URL`（可选）、`ZHIPU_API_KEY`（可选）。
- 根目录 **`.env.example`** 可复制为 **`backend/.env`** 后修改。

---

## 部署与运维

- 后端：`backend/DEPLOY.md`、`deploy.sh`；进程与反向代理按实际环境配置。
- 前端：`frontend/DEPLOY.md`、静态资源构建 `npm run build`。
- SSL 示例：`ssl-certs/`。
- 数据库安装参考：`POSTGRES_SETUP.md`。

---

## 相关文档索引

| 文档 | 内容 |
|------|------|
| [README.md](../README.md) | 快速开始、结构、特性 |
| [backend/SETUP.md](../backend/SETUP.md) | 后端安装与运行 |
| [backend/DEPLOY.md](../backend/DEPLOY.md) | 后端部署 |
| [frontend/DEPLOY.md](../frontend/DEPLOY.md) | 前端部署 |
| [POSTGRES_SETUP.md](../POSTGRES_SETUP.md) | PostgreSQL |
| [年度支出图表模块实现说明书.md](./年度支出图表模块实现说明书.md) | 年度支出图表 |
| [账单分类体系.md](../账单分类体系.md) | 分类体系 |
| [backend/scripts/README_classification_rules.md](../backend/scripts/README_classification_rules.md) | 分类规则脚本 |

---

> 若实现与本文档不符，请以代码与 OpenAPI 为准，并更新本文件。
