# 前端（家庭账单管理系统）

基于 **Vite 7 + React 18 + TypeScript** 的单页应用，UI 使用 **Ant Design 5**，状态管理为 **Zustand**，图表使用 **Recharts** 与 **ECharts**。

## 开发

```bash
cd frontend
npm install
npm run dev
```

默认开发服务器：**http://localhost:5173**。  
后端 API 默认指向 **http://localhost:8000**（见 `src/api/config.ts`）。

### 连接生产 API

构建或预览时若需使用生产环境接口，设置：

```bash
VITE_USE_PROD_API=true npm run build
```

逻辑见 `getApiBaseUrl()`：
- 显式 `VITE_USE_PROD_API=true` 时使用 `PROD_BASE_URL`
- 生产构建在非 localhost 域名下自动使用 `window.location.origin`

## 脚本

| 命令 | 说明 |
|------|------|
| `npm run dev` | 开发服务器（HMR） |
| `npm run build` | `tsc -b` 类型检查 + Vite 生产构建 |
| `npm run preview` | 本地预览 `dist` |
| `npm run lint` | ESLint |

## 目录说明

- **`src/api/`** — `client.ts`（Axios 实例与拦截器）、`config.ts`（基址与各 API 路径常量）、`services.ts`（接口封装）。
- **`src/stores/`** — 认证、账单、家庭、消息等 Zustand store。
- **`src/pages/`** — 路由页面：登录注册、仪表盘、账单、上传、消息、用户、家庭、分类规则、审计日志、设置、个人中心（含 MCP / 账单授权 Tab）等。
- **`src/components/`** — 布局、各类图表等复用组件。

路由定义见 **`src/App.tsx`**。

## 部署

详见同目录 **[DEPLOY.md](./DEPLOY.md)** 与仓库根目录 **[README.md](../README.md)**。
