# 家庭账单管理系统 - Makefile
# 简化常用开发和部署操作

.PHONY: help install dev test clean build deploy

# 默认目标
help:
	@echo "家庭账单管理系统 - 可用命令:"
	@echo ""
	@echo "开发相关:"
	@echo "  install     - 安装依赖"
	@echo "  dev         - 启动开发服务器"
	@echo "  dev-frontend - 启动前端开发服务器"
	@echo "  dev-backend  - 启动后端开发服务器"
	@echo ""
	@echo "测试相关:"
	@echo "  test        - 运行所有测试"
	@echo "  test-unit   - 运行单元测试"
	@echo "  test-api    - 运行API测试"
	@echo "  test-cov    - 运行测试并生成覆盖率报告"
	@echo ""
	@echo "代码质量:"
	@echo "  lint        - 代码检查"
	@echo "  format      - 代码格式化"
	@echo "  type-check  - 类型检查"
	@echo ""
	@echo "数据库相关:"
	@echo "  db-init     - 初始化数据库"
	@echo "  db-reset    - 重置数据库"
	@echo ""
	@echo "部署相关:"
	@echo "  build       - 构建项目"
	@echo "  deploy      - 部署到生产环境"
	@echo "  clean       - 清理临时文件"

# 安装依赖
install:
	@echo "安装后端依赖..."
	cd backend && pip install -r requirements.txt
	@echo "安装前端依赖..."
	cd frontend && npm install

# 开发服务器
dev:
	@echo "启动开发环境..."
	@echo "后端: http://127.0.0.1:8000"
	@echo "前端: http://localhost:5173"
	@echo "按 Ctrl+C 停止服务"

dev-backend:
	@echo "启动后端开发服务器..."
	cd backend && python main.py

dev-frontend:
	@echo "启动前端开发服务器..."
	cd frontend && npm run dev

# 测试
test:
	@echo "运行所有测试..."
	pytest tests/ -v

test-unit:
	@echo "运行单元测试..."
	pytest tests/ -m "unit" -v

test-api:
	@echo "运行API测试..."
	pytest tests/ -m "api" -v

test-cov:
	@echo "运行测试并生成覆盖率报告..."
	pytest tests/ --cov=backend --cov-report=html --cov-report=term

# 代码质量
lint:
	@echo "代码检查..."
	cd backend && flake8 . --max-line-length=100 --exclude=venv,env,__pycache__
	cd frontend && npm run lint

format:
	@echo "代码格式化..."
	cd backend && black . --line-length=100
	cd backend && isort .
	cd frontend && npm run format

type-check:
	@echo "类型检查..."
	cd backend && mypy . --ignore-missing-imports
	cd frontend && npm run type-check

# 数据库
db-init:
	@echo "初始化数据库..."
	cd backend && python create_tables.py

db-reset:
	@echo "重置数据库..."
	@echo "警告: 这将删除所有数据!"
	@read -p "确认继续? [y/N] " confirm && [ "$$confirm" = "y" ]
	cd backend && python scripts/reset_database.py

# 构建和部署
build:
	@echo "构建前端..."
	cd frontend && npm run build

deploy:
	@echo "部署到生产环境..."
	cd backend && ./deploy.sh
	cd frontend && ./deploy.sh

# 清理
clean:
	@echo "清理临时文件..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	cd frontend && rm -rf node_modules/.cache
	cd frontend && rm -rf dist