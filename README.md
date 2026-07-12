# Multi-User Family Bill Management System (my-bill-2)

English | **[中文](./README.zh-CN.md)**

A family bill management system built with **React + TypeScript + Vite** and **FastAPI + PostgreSQL**. It supports multi-user and family collaboration, bill import and parsing, categorization, statistical charts, system messages, and configurable classification rules.

## Overview

Import bills from **Alipay, JD.com, China Merchants Bank, WeChat Pay, Meituan**, and other sources (CSV / Excel / PDF, etc.). View income/expense trends and category breakdowns on the dashboard, and assign transactions to bill categories via **classification rules** (with optional Zhipu AI assistance).

### Core Features

- **Multi-user & families**: Registration, login, JWT, family creation and member management, shared family data views
- **Bill parsing**: Platform-specific parsers registered by `source_type` under `backend/parsers/` (Alipay, JD, CMB, WeChat, Meituan, etc.)
- **Bills & categories**: Bill CRUD, category tree, upload preview and confirm, optional duplicate detection and overwrite logic (see code and migration scripts)
- **Statistics & charts**: Dashboard, yearly expenses, monthly trends, category breakdown (Recharts / ECharts)
- **Classification rules**: Custom rules with `personal` / `family` scope (`/api/v1/classification-rules`)
- **Bill delegation**: Family members can grant create/update/delete permissions on their bills (`/api/v1/bill-delegations`)
- **Audit logs**: Track bill create/update/delete with actor and delegation metadata (`/api/v1/audit-logs`)
- **MCP**: 13 tools for agents via `/mcp` (API key management at `/api/v1/mcp/*`)
- **Messages**: Family/system message APIs and frontend pages
- **Operations**: Health checks and metrics (`/api/v1/health`), structured logging, optional Redis; Swagger disabled in production

## Tech Stack

| Layer | Choices |
|-------|---------|
| Frontend | React 18, TypeScript, Vite 7, Ant Design 5, Zustand, React Router 7, Axios, Recharts, ECharts (echarts-for-react) |
| Backend | Python 3, FastAPI, SQLAlchemy 2.x, Pydantic v2 / pydantic-settings, Uvicorn |
| Auth | JWT (python-jose), **bcrypt** passwords (passlib) |
| Data | PostgreSQL (`psycopg2-binary` / `asyncpg`); migrations in `backend/migrations/` |
| Optional | Zhipu AI (`ZHIPU_API_KEY` for smart classification), Redis (`REDIS_URL`) |

## Repository Layout

```text
my-bill-2/
├── backend/                 # FastAPI app (often run from backend/)
│   ├── api/                 # Routes: auth, bills, upload, families, users, messages, system_config, classification_rules, health, mcp, audit-logs, bill-delegations
│   ├── bill_mcp/            # MCP tool server (Family Bills MCP)
│   ├── config/              # settings, database, logging; environments/*.env samples
│   ├── core/                # Middleware, exceptions
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic models
│   ├── services/            # Business logic
│   ├── parsers/             # Platform bill parsers
│   ├── migrations/          # SQL/Python migration scripts
│   ├── main.py              # FastAPI entry
│   ├── run.py               # Alternate uvicorn entry
│   ├── create_tables.py     # Core tables only (make db-init); run backend/migrations/*.sql for the rest
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/             # client, config (API base URL & endpoints), services
│   │   ├── components/      # Layout, charts, etc.
│   │   ├── pages/           # Login, dashboard, bills, upload, family, messages, users, rules, settings, etc.
│   │   ├── stores/          # Zustand
│   │   └── types/
│   └── package.json
├── database/
│   └── init.sql             # Reference SQL (follow actual migrations and models)
├── docs/                    # Project notes and feature docs
├── scripts/                 # Analysis, troubleshooting, utilities
├── .env.example             # Env template (copy to backend/.env; see below)
├── Makefile                 # install, dev-backend, dev-frontend, test, db-init, etc.
├── pytest.ini               # Pytest config (add tests/ as needed)
├── README.md                # English README (GitHub default)
└── README.zh-CN.md          # Chinese README
```

## Requirements

- **Node.js** 18+
- **Python** 3.9+ (match `backend/requirements.txt`)
- **PostgreSQL** 12+

## Quick Start (Makefile recommended)

```bash
git clone <repository-url>
cd my-bill-2

# Copy env template from repo root to backend/.env (backend BASE_DIR is backend/)
cp .env.example backend/.env
# Edit backend/.env: at minimum set DATABASE_URL and SECRET_KEY (≥32 chars)

# Install dependencies
make install

# Initialize core database tables (runs create_tables.py under backend/)
make db-init
# Apply incremental SQL as needed, e.g.:
# psql $DATABASE_URL -f backend/migrations/add_audit_logs.sql

# Run in two terminals (`make dev` only prints URLs; use dev-backend / dev-frontend)
make dev-backend    # http://127.0.0.1:8000  (runs python main.py)
make dev-frontend   # http://localhost:5173
```

Useful commands: `make help`, `make test` (requires `tests/` and test cases), `make lint`, `make format`, `make build`.

### Environment Variables (essentials)

- Load order in `backend/config/settings.py`: **`backend/.env` first**, else `backend/config/environments/{ENVIRONMENT}.env`.
- **SECRET_KEY**: at least 32 characters.
- **CORS_ORIGINS**: comma-separated; defaults include `localhost:5173`, etc.
- **ALLOWED_EXTENSIONS**: per `settings`; may include `.csv,.xlsx,.xls,.pdf`, etc.
- **ZHIPU_API_KEY**: optional, for AI classification.
- **ACCESS_TOKEN_EXPIRE_MINUTES**: default **240** in `settings.py`; production env files often use 30.
- Root `.env.example` maps to backend fields; `Field` definitions in `settings.py` are authoritative.

### Frontend API Base URL

- Development defaults to `http://localhost:8000` (see `frontend/src/api/config.ts`).
- Production builds on a non-localhost host auto-use `window.location.origin`.
- To force the production API URL, set **`VITE_USE_PROD_API=true`** (see `getApiBaseUrl()`).

## Main Frontend Routes

| Path | Description |
|------|-------------|
| `/login`, `/register` | Login and registration |
| `/dashboard`, `/family-dashboard` | Dashboards (stats and charts) |
| `/bills` | Bill list and management |
| `/upload` | Upload and import |
| `/messages` | Messages |
| `/users` | User management (role-based) |
| `/family` | Family management |
| `/classification-rules` | Classification rules |
| `/audit-logs` | Audit logs |
| `/settings` | Settings |
| `/profile` | Profile (tabs: MCP, bill delegation) |
| `/mcp-settings` | Redirects to `/profile?tab=mcp` |

## Backend API & Docs

- Dev Swagger: **http://localhost:8000/docs** (may be disabled when `ENVIRONMENT=production`; check config).
- API prefix: **`/api/v1`**.
- Examples:
  - `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`
  - `GET|POST /api/v1/bills`, `GET /api/v1/bills/stats`, finance summary and chart endpoints
  - `POST /api/v1/upload` (direct import), `GET /api/v1/upload/history`
  - `GET /api/v1/audit-logs`, `GET|POST /api/v1/bill-delegations`
  - `GET /api/v1/mcp/settings`, `GET /api/v1/mcp/info`
  - `GET /api/v1/health/...` health checks
- MCP agent endpoint: **`/mcp`** (13 tools; see `docs/project_overview.md`)

See OpenAPI for the full list.

## Data Model (summary)

Core entities: `User`, `Family`, `FamilyMember`, `Bill`, `BillCategory`, `Message`, `MessageAction`, `SystemConfig`, `ClassificationRule`, `McpApiKey`, `AuditLog`, `BillDelegation`. See `backend/models/` for relationships and fields.

## Security

- **Passwords**: stored as **bcrypt** hashes (not plaintext or SHA256).
- **Tokens**: JWT; middleware includes token refresh and rate limiting (`backend/core/middleware.py`).
- **Production**: strong `SECRET_KEY`, HTTPS, tight CORS, disable Swagger as needed.

## Deployment & More Docs

- Backend: `backend/DEPLOY.md`, `backend/deploy.sh`
- Frontend: `frontend/DEPLOY.md`, `frontend/deploy.sh`
- PostgreSQL: `POSTGRES_SETUP.md`
- Architecture overview: `docs/project_overview.md`
- Yearly expense charts: `docs/年度支出图表模块实现说明书.md`
- Bill category system: `账单分类体系.md`
- Classification rule scripts: `backend/scripts/README_classification_rules.md`

## Troubleshooting

- **Database connection failed**: Check PostgreSQL service, `DATABASE_URL`, firewall, and DB user permissions.
- **CORS**: Add your frontend origin to `CORS_ORIGINS`.
- **Upload failed**: Check `ALLOWED_EXTENSIONS`, `MAX_FILE_SIZE`, `backend/uploads` permissions, and whether a parser exists for the `source_type`.

---

When maintaining docs, keep `docs/project_overview.md` and this README in sync with `backend/config/settings.py` and route registration.
