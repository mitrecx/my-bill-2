# 后端设置说明

> 配置字段以 **`config/settings.py`** 为准；环境变量加载顺序见该文件（优先 **`backend/.env`**，否则 `config/environments/{ENVIRONMENT}.env`）。仓库根目录的 **`.env.example`** 可复制为 **`backend/.env`** 后修改。

## 环境要求

- Python 3.9+（推荐与生产一致）
- PostgreSQL 12+
- pip

## 安装步骤

### 1. 安装依赖

在 `backend/` 目录下：

```bash
pip install -r requirements.txt
```

### 2. 环境变量配置

在 **`backend/`** 下创建 **`.env`**（或由仓库根目录 `cp ../.env.example .env`），示例字段：

```bash
ENVIRONMENT=development
DEBUG=true
HOST=127.0.0.1
PORT=8000

# 数据库（必填）
DATABASE_URL=postgresql://user:password@localhost:5432/bills_db

# 安全（SECRET_KEY 至少 32 字符）
SECRET_KEY=your-very-secret-key-at-least-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS：逗号分隔多个源
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# 上传与日志
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760
ALLOWED_EXTENSIONS=.csv,.xlsx,.xls,.pdf
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# 可选
# REDIS_URL=redis://localhost:6379/0
# ZHIPU_API_KEY=
```

### 3. 数据库设置

#### PostgreSQL 数据库配置

```bash
# 连接远程数据库进行测试
psql -h localhost -U josie -d bills_db -c "SELECT 1;"
# 输入密码: bills_password_2024

# 如果需要初始化数据库表结构，可以运行：
psql -h localhost -U josie -d bills_db -f init.sql
```

### 4. 运行项目

#### 开发模式
```bash
python run.py
```

#### 或使用uvicorn直接运行
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API 文档

启动服务后，访问以下地址查看API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
backend/
├── api/                    # API 路由（见 api/__init__.py 汇总）
│   ├── auth.py            # 用户认证
│   ├── bills.py           # 账单管理
│   ├── upload.py          # 文件上传
│   ├── families.py        # 家庭
│   ├── users.py           # 用户管理
│   ├── messages.py        # 消息
│   ├── system_config.py   # 系统配置
│   ├── classification_rules.py  # 分类规则
│   └── health.py          # 健康检查
├── config/                # 配置文件
│   ├── database.py        # 数据库配置
│   └── settings.py        # 应用设置
├── models/                # 数据模型
│   ├── user.py           # 用户模型
│   ├── family.py         # 家庭模型
│   └── bill.py           # 账单模型
├── schemas/               # Pydantic模型
│   ├── auth.py           # 认证相关
│   ├── bills.py          # 账单相关
│   └── upload.py         # 上传相关
├── parsers/               # 文件解析器
│   ├── base_parser.py    # 基础解析器
│   ├── alipay_parser.py  # 支付宝解析器
│   ├── jd_parser.py      # 京东解析器
│   └── cmb_parser.py     # 招商银行解析器
├── utils/                 # 工具函数
│   ├── security.py       # 安全工具
│   └── validators.py     # 验证工具
├── main.py               # 主应用
├── run.py                # 启动脚本
└── requirements.txt      # 依赖列表
```

## 核心功能

### 1. 用户认证
- 用户注册/登录
- JWT Token管理
- 密码加密存储

### 2. 家庭管理
- 多用户家庭系统
- 角色权限管理(admin/member/viewer)
- 数据隔离

### 3. 文件解析
- 支付宝 CSV、京东 CSV、招商银行 PDF、微信支付 Excel、美团 CSV 等（见 `parsers/__init__.py`）
- 分类规则与可选 AI 辅助（`services/ai_classification_service.py`、智谱 API Key）

### 4. 账单管理
- 账单CRUD操作
- 高级筛选和搜索
- 统计分析功能
- 分页查询

### 5. 数据安全
- 数据访问权限控制
- 原始数据保存
- 错误处理和日志记录

## 开发说明

### 添加新的文件解析器

1. 在 `parsers/` 目录创建新解析器
2. 继承 `BaseParser` 类
3. 实现 `parse_file()` 和 `parse_content()` 方法
4. 在 `parsers/__init__.py` 中注册

### 添加新的API端点

1. 在 `api/` 目录创建新路由文件
2. 在 `schemas/` 目录创建对应的数据模型
3. 在 `api/__init__.py` 中注册路由

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查DATABASE_URL配置
   - 确认数据库服务运行
   - 验证用户权限

2. **导入错误**
   - 检查依赖安装
   - 确认Python路径配置

3. **文件上传失败**
   - 检查文件格式支持
   - 确认上传目录权限
   - 验证文件大小限制

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
grep ERROR logs/app.log
```