# 部署脚本使用说明

## 概述

`deploy.sh` 脚本已经优化，支持智能依赖管理，避免每次部署都重新安装依赖，大大提升部署效率。

## 使用方法

### 1. 智能部署（推荐）
```bash
./deploy.sh
```
- 自动检测是否需要安装依赖
- 只有在首次部署或 `requirements.txt` 文件有变化时才会安装依赖
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

## 智能检测机制

脚本通过以下方式判断是否需要安装依赖：

1. **首次部署检测**：如果服务器上不存在 `.deps_installed` 标记文件，说明是首次部署，会安装依赖
2. **文件变化检测**：比较 `requirements.txt` 和 `.deps_installed` 文件的修改时间，如果 `requirements.txt` 更新，会重新安装依赖
3. **标记文件管理**：成功安装依赖后会创建 `.deps_installed` 标记文件

## 部署配置

部署脚本从仓库根目录的 **`.env.deploy`** 读取目标服务器（不入库）：

```bash
cp .env.deploy.example .env.deploy
# 编辑 DEPLOY_REMOTE_USER / DEPLOY_REMOTE_HOST / DEPLOY_PUBLIC_URL
```

## 服务管理（systemd）

生产环境通过 **systemd** 托管后端，单元文件见 `deploy/family-bills-backend.service`。

```bash
# 部署并同步 systemd 单元
./deploy.sh

# 运维命令
./deploy.sh restart
./deploy.sh status
./deploy.sh logs
./deploy.sh stop
```

服务监听 `127.0.0.1:8000`，由 nginx 反代；日志优先用 `journalctl -u family-bills-backend`。

本地开发仍可使用 `python run.py` 或 `python main.py`。

## 部署流程

1. **压缩本地文件**：排除不必要的文件（缓存、日志等）
2. **上传到服务器**：通过 SCP 上传压缩包
3. **远程部署**：
   - 备份旧版本
   - 解压新版本
   - 设置环境变量
   - 智能安装依赖（根据参数和检测结果）
   - 同步 systemd 单元并重启服务
   - 健康检查
4. **清理临时文件**

## 性能提升

- **首次部署**：与原来相同，需要安装依赖
- **后续部署**（无依赖变化）：节省 2-5 分钟的依赖安装时间
- **依赖更新时**：自动检测并安装，无需手动干预

## 数据库迁移

`create_tables.py` 仅创建核心表。若代码有 schema 变更，部署后需在服务器执行对应 SQL，例如：

```bash
psql $DATABASE_URL -f migrations/add_audit_logs.sql
psql $DATABASE_URL -f migrations/add_mcp_api_keys.sql
psql $DATABASE_URL -f migrations/add_bill_delegations.sql
```

完整列表见 `backend/migrations/`。

## MCP

部署后 MCP 端点为 **`https://<your-domain>/mcp`**（与 REST `/api/v1` 并列，非其子路径）。需在应用设置中生成 MCP API Key。

## 注意事项

1. 确保脚本有执行权限：`chmod +x deploy.sh`
2. 确保已配置 SSH 密钥认证到目标服务器
3. 如果遇到依赖问题，可以使用 `--deps` 参数强制重新安装
4. 部署完成后会显示服务地址和健康检查链接
5. 生产环境 Swagger（`/docs`）默认关闭

## 故障排除

- **依赖安装失败**：使用 `./deploy.sh --deps` 强制重新安装
- **服务启动失败**：`./deploy.sh status` 或 `./deploy.sh logs`；也可 `journalctl -u family-bills-backend -n 50`
- **权限问题**：确保用户对目标目录有写权限