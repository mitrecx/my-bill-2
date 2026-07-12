# 前端部署脚本使用说明

## 概述

`deploy.sh` 脚本用于自动化部署前端应用到 `bill.mitrecx.top` 服务器，支持智能依赖管理和自动nginx配置。

## 使用方法

### 1. 智能部署（推荐）
```bash
./deploy.sh
```
- 自动检测是否需要安装依赖
- 只有在首次部署或 `package.json`/`package-lock.json` 文件有变化时才会安装依赖
- 大多数情况下推荐使用此方式

### 2. 强制重新安装依赖
```bash
./deploy.sh --deps
```
- 强制重新安装所有依赖
- 适用于依赖出现问题或需要清理环境的情况

### 3. 跳过依赖安装
```bash
./deploy.sh --no-deps
```
- 完全跳过依赖安装步骤
- 适用于确定依赖没有变化，只是代码更新的情况
- 部署速度最快

## 部署流程

1. **智能依赖检测**：根据参数和文件变化检测是否需要安装依赖
2. **安装依赖**：使用 `npm install` 安装前端依赖（如果需要）
3. **构建项目**：使用 `npm run build` 构建生产版本
4. **压缩文件**：将 `dist` 目录打包为 tar.gz 文件
5. **上传到服务器**：通过 SCP 上传压缩包
6. **远程部署**：
   - 备份旧版本
   - 解压新版本到 `/var/www/family-bills-frontend`
   - 设置文件权限
   - **`nginx -t` 与 `reload`（不覆盖站点配置）**
7. **清理临时文件**

## HTTPS / Nginx（重要）

**`deploy.sh` 不再写入或覆盖 `/etc/nginx/conf.d/` 下的站点配置。**

原因：旧版脚本每次部署都会把 `ssl_certificate` 固定为 `/etc/nginx/ssl/bill.mitrecx.top.pem`。若服务器上实际使用的是 **Let’s Encrypt**（`/etc/letsencrypt/live/...`）或更新的证书，而 `/etc/nginx/ssl/` 里只是**曾经拷贝的旧文件**，覆盖后 Nginx 会重新指向这些过期副本，表现为「部署前证书正常、部署后浏览器提示过期」。

- **日常发版**：只更新前端静态文件，**不修改**证书路径与 vhost。
- **首次上架 / 改 Nginx**：在服务器上单独配置，或使用仓库内 **`ssl-certs/`**（如 `renew-ssl.sh`、`deploy-ssl.sh`）、根目录 **`family-bills-https.conf`** 作为参考。

示例站点能力（需在服务器上的 Nginx 配置中自行维护）：

- SPA 路由、`/api/` 反代到后端、静态缓存、Gzip、安全头等。

## 访问地址

部署完成后，可以通过以下地址访问：

- **前端应用**：https://bill.mitrecx.top
- **REST API**：https://bill.mitrecx.top/api/v1/...（经 Nginx 反代至后端）
- **MCP 端点**：https://bill.mitrecx.top/mcp
- **Swagger 文档**：仅开发环境可用（`http://localhost:8000/docs`）；生产 `ENVIRONMENT=production` 时关闭，**无** `/api/docs`

## 智能检测机制

脚本通过以下方式判断是否需要安装依赖：

1. **首次部署检测**：如果不存在 `.deps_installed` 标记文件，说明是首次部署
2. **文件变化检测**：比较 `package.json` 和 `package-lock.json` 的修改时间
3. **标记文件管理**：成功安装依赖后会创建 `.deps_installed` 标记文件

## 性能提升

- **首次部署**：与原来相同，需要安装依赖和构建
- **后续部署**（无依赖变化）：节省 1-3 分钟的依赖安装时间
- **依赖更新时**：自动检测并安装，无需手动干预

## 前置要求

1. **本地环境**：
   - Node.js 和 npm 已安装
   - 已配置 SSH 密钥认证到目标服务器

2. **服务器环境**：
   - Nginx 已安装
   - 用户具有 sudo 权限
   - `/var/www` 目录存在且可写

## 注意事项

1. 确保脚本有执行权限：`chmod +x deploy.sh`
2. 首次部署可能需要较长时间（依赖安装 + 构建）
3. 如果遇到权限问题，检查服务器上的 sudo 配置
4. 部署过程中会自动备份旧版本到 `${REMOTE_PATH}-backup`

## 故障排除

- **依赖安装失败**：使用 `./deploy.sh --deps` 强制重新安装
- **构建失败**：检查本地 Node.js 版本和依赖兼容性
- **Nginx 配置错误**：检查服务器上的 nginx 错误日志
- **权限问题**：确保用户对 `/var/www` 目录有写权限
- **上传失败**：检查 SSH 连接和网络状况

## 与后端集成

前端部署脚本与后端部署脚本可以独立使用：

1. **完整部署**：先部署后端，再部署前端
2. **前端更新**：只运行前端部署脚本
3. **后端更新**：只运行后端部署脚本

通过 Nginx 的 API 代理配置，前端可以无缝访问后端服务。