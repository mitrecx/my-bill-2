# PostgreSQL 数据库设置指南

本项目已从SQLite迁移到PostgreSQL数据库。请按照以下步骤设置PostgreSQL数据库。

## 1. 安装PostgreSQL

### macOS (使用Homebrew)
```bash
# 安装PostgreSQL
brew install postgresql

# 启动PostgreSQL服务
brew services start postgresql

# 创建数据库用户（可选）
createuser -s postgres
```

### Ubuntu/Debian
```bash
# 更新包列表
sudo apt update

# 安装PostgreSQL
sudo apt install postgresql postgresql-contrib

# 启动PostgreSQL服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 切换到postgres用户
sudo -u postgres psql

# 在psql中设置密码
\password postgres
```

### Windows
1. 从 [PostgreSQL官网](https://www.postgresql.org/download/windows/) 下载安装程序
2. 运行安装程序，记住设置的密码
3. 确保PostgreSQL服务正在运行

## 2. 配置数据库连接

### 编辑环境变量文件
在 `backend/.env` 文件中配置数据库连接：

```env
# 数据库配置
DATABASE_URL=postgresql://josie:bills_password_2024@localhost:5432/bills_db

# JWT配置
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 应用配置
DEBUG=False
HOST=127.0.0.1
PORT=8000
```

**重要：** 请将 `your_password` 替换为你的PostgreSQL密码。

## 3. 初始化数据库

### 方法一：使用自动化脚本（推荐）
```bash
cd backend
python setup_postgres.py
```

这个脚本会自动：
- 创建数据库 `bills_db`
- 创建所有必要的表
- 插入默认的账单分类

### 方法二：手动设置

1. **创建数据库**
```bash
# 连接到PostgreSQL
psql -U postgres -h localhost

# 创建数据库
CREATE DATABASE bills_db;

# 退出
\q
```

2. **创建表结构**
```bash
cd backend
python create_tables.py
```

3. **运行初始化SQL**
```bash
psql -U postgres -h localhost -d bills_db -f ../database/init.sql
```

## 4. 验证设置

### 检查数据库连接
```bash
cd backend
python -c "from config.database import engine; print('数据库连接成功!' if engine.connect() else '连接失败')"
```

### 检查表是否创建
```bash
# 连接远程数据库
psql -h localhost -U josie -d bills_db -c "\dt"
# 输入密码: bills_password_2024
```

应该看到以下表：
- users
- families
- family_members
- bill_categories
- bills
- upload_records

## 5. 启动应用

```bash
cd backend
python main.py
```

## 常见问题

### Q: 连接被拒绝
**A:** 确保PostgreSQL服务正在运行：
```bash
# macOS
brew services restart postgresql

# Ubuntu/Debian
sudo systemctl restart postgresql
```

### Q: 认证失败
**A:** 检查用户名和密码是否正确，或重置密码：
```bash
sudo -u postgres psql
\password postgres
```

### Q: 数据库不存在
**A:** 运行设置脚本或手动创建数据库：
```bash
python setup_postgres.py
```

### Q: 权限不足
**A:** 确保PostgreSQL用户有创建数据库的权限：
```sql
ALTER USER postgres CREATEDB;
```

## 数据迁移

如果你之前使用SQLite并有数据需要迁移，请：

1. 备份SQLite数据
2. 设置PostgreSQL数据库
3. 使用数据导出/导入工具迁移数据
4. 或者重新注册用户和上传账单文件

## 生产环境建议

1. **安全性**：
   - 使用强密码
   - 限制数据库访问IP
   - 启用SSL连接

2. **性能**：
   - 调整PostgreSQL配置
   - 设置适当的连接池大小
   - 定期维护和优化

3. **备份**：
   - 设置定期备份
   - 测试恢复流程

```bash
# 备份数据库
pg_dump -U postgres -h localhost bills_db > backup.sql

# 恢复数据库
psql -U postgres -h localhost bills_db < backup.sql
```