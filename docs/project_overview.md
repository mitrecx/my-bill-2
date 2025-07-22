
# 项目梳理文档

## 1. 项目概述

`my-bills-2` 是一个功能完善的个人账单管理系统，旨在提供一个清晰、高效的方式来跟踪、管理和分析个人财务。系统采用现代化的技术栈，前后端分离，为用户提供了丰富的功能，包括账单导入、分类、统计分析、家庭共享等。

## 2. 技术栈

项目采用了前后端分离的架构，具体技术栈如下：

### 2.1 后端 (`backend`)

- **框架**: [FastAPI](https://fastapi.tiangolo.com/) - 一个现代化、高性能的 Python Web 框架，用于构建 API。
- **数据库**: [PostgreSQL](https://www.postgresql.org/) - 一款功能强大的开源对象-关系型数据库系统。
- **ORM**: [SQLAlchemy](https://www.sqlalchemy.org/) - 提供了强大的 SQL 工具包和 ORM。
- **数据库迁移**: [Alembic](https://alembic.sqlalchemy.org/) - 一个轻量级的数据库迁移工具，与 SQLAlchemy 配合使用。
- **认证与安全**:
    - `python-jose` & `passlib`: 用于 JWT 令牌的生成、验证和密码哈希。
- **数据处理与验证**:
    - `pydantic`: 用于数据验证和设置管理。
    - `pandas`: 用于处理和分析账单数据，特别是在文件导入时。
- **PDF 处理**: `pdfplumber` - 用于从 PDF 文件中提取账单信息。
- **异步支持**: `syncpg` - 提供异步数据库驱动。
- **部署**: 使用 `uvicorn` 作为 ASGI 服务器。

### 2.2 前端 (`frontend`)

- **框架**: [React](https://react.dev/) - 用于构建用户界面的 JavaScript 库。
- **构建工具**: [Vite](https://vitejs.dev/) - 提供快速的冷启动和模块热更新（HMR）。
- **语言**: [TypeScript](https://www.typescriptlang.org/) - 为 JavaScript 添加了类型系统。
- **路由**: [React Router](https://reactrouter.com/) - 用于在 React 应用中处理路由。
- **UI 组件库**: [Ant Design](https://ant.design/) - 一套企业级的 UI 设计语言和 React UI 库。
- **状态管理**: [Zustand](https://zustand-demo.pmnd.rs/) - 一个小型、快速、可扩展的 React 状态管理解决方案。
- **HTTP 客户端**: [Axios](https://axios-http.com/) - 用于浏览器和 Node.js 的基于 Promise 的 HTTP 客户端。
- **图表**: [Recharts](https://recharts.org/) - 一个基于 React 的组合式图表库。

## 3. 项目结构

### 3.1 后端结构

后端代码位于 `backend/` 目录下，遵循模块化的设计原则：

- `api/`: 存放所有 API 路由模块，每个文件对应一个功能模块（如 `bills.py`, `users.py`）。
- `config/`: 包含应用的配置，如数据库连接、环境变量和日志配置。
- `core/`: 核心组件，如异常处理和中间件。
- `models/`: 定义数据库模型（基于 SQLAlchemy）。
- `schemas/`: 定义数据验证模型（基于 Pydantic）。
- `services/`: 业务逻辑层，处理复杂的操作。
- `parsers/`: 用于解析不同来源（如支付宝、微信）的账单文件。
- `main.py`: FastAPI 应用的入口文件，负责初始化、中间件和路由注册。

### 3.2 前端结构

前端代码位于 `frontend/` 目录下，采用了典型的 React 应用结构：

- `src/`:
    - `api/`: 存放与后端交互的 API 服务和客户端配置。
    - `components/`: 可复用的 React 组件。
    - `hooks/`: 自定义 React Hooks。
    - `pages/`: 应用的各个页面组件。
    - `stores/`: 全局状态管理（Zustand stores）。
    - `types/`: TypeScript 类型定义。
    - `App.tsx`: 应用的主组件，负责路由配置和整体布局。
    - `main.tsx`: 应用的入口文件。

## 4. 核心功能

1.  **用户认证**:
    - 支持用户注册和登录。
    - 使用 JWT (JSON Web Tokens) 进行会话管理。
    - `ProtectedRoute` 机制保护需要登录才能访问的页面。

2.  **账单管理**:
    - 支持通过上传文件（CSV, PDF）批量导入账单。
    - 系统能够自动解析不同银行或平台的账单格式。
    - 提供账单的增、删、改、查功能。
    - 支持强大的过滤和搜索功能。

3.  **数据可视化**:
    - 在仪表盘（Dashboard）页面以图表形式展示收支概览和趋势。
    - `StatsPage` 提供更详细的统计分析。

4.  **家庭共享**:
    - 用户可以创建家庭组，并邀请其他成员加入。
    - 家庭成员可以共享和共同管理账单。

5.  **消息系统**:
    - 用于家庭成员之间的通信或系统通知。

6.  **用户管理**:
    - （管理员功能）可以查看和管理系统中的所有用户。

## 5. 启动与部署

- **本地开发**:
    - 后端: `cd backend && uvicorn main:app --reload`
    - 前端: `cd frontend && npm run dev`
- **部署**:
    - 提供了 `deploy.sh` 脚本用于自动化部署。
    - 详细的部署指南可以参考 `DEPLOY.md` 文件。

## 6. 总结

`my-bills-2` 是一个结构清晰、技术栈现代化的全栈项目。它不仅展示了如何使用 FastAPI 和 React 构建一个功能丰富的 Web 应用，还体现了良好的软件工程实践，如模块化设计、配置管理和自动化部署。该项目可以作为学习和实践全栈开发的优秀范例。 