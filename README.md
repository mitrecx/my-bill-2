# 多用户家庭账单管理系统

一个基于 React + FastAPI 的现代化家庭账单管理系统，支持多用户协作、自动账单解析、智能分类统计等功能。

## 📋 项目概述

本系统专为家庭财务管理设计，支持从支付宝、京东、招商银行等平台导入账单数据，提供直观的数据可视化和统计分析功能，帮助家庭更好地管理财务状况。

### 核心特性

- 🔐 **多用户系统** - 支持用户注册、登录、权限管理
- 👨‍👩‍👧‍👦 **家庭协作** - 多用户可加入同一家庭，共享账单数据
- 📄 **智能解析** - 自动解析支付宝CSV、京东CSV、招商银行PDF账单文件
- 📊 **数据可视化** - 丰富的图表展示收支趋势、分类统计
- 🔍 **智能搜索** - 支持按时间、金额、类型、来源等多维度筛选
- 📱 **响应式设计** - 完美支持桌面和移动设备

## 🛠 技术栈

### 前端技术
- **框架**: React 19 + TypeScript
- **构建工具**: Vite 7
- **UI库**: Ant Design 5
- **状态管理**: Zustand
- **路由**: React Router Dom 7
- **图表**: Recharts
- **HTTP客户端**: Axios

### 后端技术
- **框架**: FastAPI (Python)
- **数据库**: PostgreSQL
- **ORM**: SQLAlchemy
- **认证**: JWT Token
- **文档**: Swagger/OpenAPI

### 部署环境
- **服务器**: Linux (CentOS/RHEL)
- **反向代理**: 可配置 Nginx
- **进程管理**: systemd 或 PM2

## 📁 项目结构

```
my-bills-2/
├── frontend/                 # 前端项目
│   ├── src/
│   │   ├── api/             # API接口层
│   │   ├── components/      # 公共组件
│   │   ├── pages/           # 页面组件
│   │   ├── stores/          # 状态管理
│   │   ├── types/           # TypeScript类型定义
│   │   └── main.tsx         # 入口文件
│   ├── package.json
│   └── vite.config.ts
├── backend/                  # 后端项目
│   ├── config/              # 配置文件
│   ├── models/              # 数据模型
│   ├── api/                 # API路由
│   ├── core/                # 核心功能
│   ├── utils/               # 工具函数
│   ├── main_production.py   # 生产环境入口
│   └── requirements.txt     # Python依赖
├── database/                # 数据库相关
│   └── schema.sql          # 数据库结构
├── bills/                   # 示例账单文件
└── README.md               # 项目文档
```

## 🚀 快速开始

### 环境要求

- Node.js 18+
- Python 3.9+
- PostgreSQL 12+

### 1. 克隆项目

```bash
git clone <repository-url>
cd my-bills-2
```

### 2. 数据库设置

#### 安装 PostgreSQL

**macOS:**
```bash
# 使用 Homebrew 安装
brew install postgresql
brew services start postgresql
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Windows:**
下载并安装 PostgreSQL 官方安装包：https://www.postgresql.org/download/windows/

#### 配置数据库

```bash
# 创建数据库和用户
sudo -u postgres psql << EOF
CREATE DATABASE bills_db;
CREATE USER postgres WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE bills_db TO postgres;
\q
EOF

# 使用自动化脚本初始化数据库（推荐）
cd backend
python setup_postgres.py

# 或者手动导入数据库结构
psql -U postgres -d bills_db -f init.sql
```

#### 环境配置

在 `backend` 目录下创建 `.env` 文件：

```bash
DATABASE_URL=postgresql://josie:bills_password_2024@localhost:5432/bills_db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=True
HOST=127.0.0.1
PORT=8000
```

> 📝 **注意**: 请根据实际情况修改数据库连接参数，生产环境请使用强密码。

### 3. 后端部署

```bash
cd backend

# 安装系统依赖（CentOS/RHEL）
sudo yum install -y postgresql-devel python3-devel gcc

# 安装Python依赖
pip3 install -r requirements.txt

# 配置环境变量（可选）
export DATABASE_URL="postgresql://josie:bills_password_2024@localhost/bills_db"

# 启动后端服务
python3 main_production.py
```

### 4. 前端部署

```bash
cd frontend

# 安装依赖
npm install

# 开发环境启动
npm run dev

# 生产环境构建
npm run build
```

## 🔧 配置说明

### 后端配置

主要配置文件：`backend/config/settings.py`

```python
class Settings:
    app_name: str = "家庭账单管理系统"
    debug: bool = False
    secret_key: str = "your-secret-key"
    
    # 数据库配置
    database_url: str = "postgresql://josie:bills_password_2024@localhost:5432/bills_db"
    
    # CORS配置
    allowed_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://yourdomain.com"
    ]
```

### 前端配置

主要配置文件：`frontend/src/api/config.ts`

```typescript
export const API_CONFIG = {
  // 开发环境API地址
  BASE_URL: 'http://localhost:8000/api/v1',
  
  // 生产环境API地址
  PROD_BASE_URL: 'http://jo.mitrecx.top:8000/api/v1',
  
  // 请求超时时间
  TIMEOUT: 30000,
}
```

## 📖 使用指南

### 1. 用户注册和登录

1. 访问前端地址，点击"立即注册"
2. 填写用户名、邮箱、姓名、密码
3. 注册成功后自动登录进入仪表板

### 2. 账单文件上传

1. 进入"文件上传"页面
2. 选择家庭（如果已创建）
3. 拖拽或点击上传账单文件
4. 支持格式：
   - 支付宝：CSV格式
   - 京东：CSV格式  
   - 招商银行：PDF格式

### 3. 账单管理

1. 在"账单管理"页面查看所有账单
2. 使用搜索和筛选功能找到特定账单
3. 支持按时间、金额、类型、来源筛选
4. 可以编辑或删除账单记录

### 4. 统计分析

1. 在"统计分析"页面查看财务概览
2. 查看收支趋势图表
3. 分析各分类支出占比
4. 支持时间范围筛选

## 🗄️ 数据库结构

### 主要数据表

- `users` - 用户信息
- `families` - 家庭信息  
- `family_members` - 家庭成员关系
- `bills` - 账单记录
- `bill_categories` - 账单分类
- `upload_records` - 上传记录

### 核心关系

```
Users (1:N) FamilyMembers (N:1) Families
Families (1:N) Bills (N:1) BillCategories
Users (1:N) UploadRecords
```

## 🌐 API文档

后端提供完整的 OpenAPI/Swagger 文档：

- 开发环境: http://localhost:8000/docs
- 生产环境: http://jo.mitrecx.top:8000/docs

### 主要API端点

- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取当前用户信息
- `GET /api/v1/bills` - 获取账单列表
- `GET /api/v1/bills/stats` - 获取统计数据
- `POST /api/v1/upload/preview` - 文件预览
- `POST /api/v1/upload/confirm` - 确认上传

## 🔐 安全说明

### 认证机制
- JWT Token 认证
- Token 过期时间管理
- 密码哈希存储（SHA256）

### 数据安全
- SQL注入防护（SQLAlchemy ORM）
- CORS跨域访问控制
- 敏感信息加密存储

### 文件安全
- 文件类型验证
- 文件大小限制（10MB）
- 上传目录权限控制

## 🚀 生产部署

### 后端生产部署

```bash
# 使用 systemd 管理服务
sudo tee /etc/systemd/system/bills-backend.service > /dev/null <<EOF
[Unit]
Description=Family Bills Backend
After=network.target

[Service]
Type=simple
User=josie
WorkingDirectory=/home/josie/apps/family-bills-backend
ExecStart=/usr/bin/python3 main_production.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
sudo systemctl enable bills-backend
sudo systemctl start bills-backend
```

### 前端生产部署

```bash
# 构建生产版本
npm run build

# 使用 Nginx 托管静态文件
sudo tee /etc/nginx/conf.d/bills-frontend.conf > /dev/null <<EOF
server {
    listen 80;
    server_name yourdomain.com;
    
    root /path/to/frontend/dist;
    index index.html;
    
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF
```

## 🐛 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查PostgreSQL服务状态
   sudo systemctl status postgresql
   
   # 检查数据库连接
   psql -h localhost -U josie -d bills_db -c "SELECT 1"
   ```

2. **CORS跨域错误**
   - 检查后端 `allowed_origins` 配置
   - 确认前端访问地址在允许列表中

3. **文件上传失败**
   - 检查文件格式和大小
   - 确认上传目录权限
   - 查看后端日志

### 日志查看

```bash
# 后端日志
tail -f /home/josie/apps/family-bills-backend/app.log

# 系统服务日志
sudo journalctl -u bills-backend -f
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📝 更新日志

### v1.0.0 (2025-07-10)
- ✅ 完成基础用户认证系统
- ✅ 实现多用户家庭协作功能
- ✅ 支持支付宝、京东、招商银行账单解析
- ✅ 完成数据可视化和统计分析
- ✅ 完成生产环境部署配置

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系信息

- 项目维护者: [Your Name]
- 邮箱: [your.email@example.com]
- 项目地址: [https://github.com/username/my-bills-2]

---

**🎉 感谢使用家庭账单管理系统！如有问题请提交 Issue 或 Pull Request。**