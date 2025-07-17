#!/bin/bash

# 后端服务部署脚本
# 部署到 jo.mitrecx.top 服务器
# 使用方法:
#   ./deploy.sh           # 正常部署，智能检测是否需要安装依赖
#   ./deploy.sh --deps     # 强制重新安装依赖
#   ./deploy.sh --no-deps  # 跳过依赖安装

set -e

# 解析命令行参数
FORCE_DEPS=false
SKIP_DEPS=false

for arg in "$@"; do
    case $arg in
        --deps)
            FORCE_DEPS=true
            shift
            ;;
        --no-deps)
            SKIP_DEPS=true
            shift
            ;;
        *)
            echo "未知参数: $arg"
            echo "使用方法: $0 [--deps|--no-deps]"
            exit 1
            ;;
    esac
done

echo "开始部署家庭账单管理系统后端服务..."

# 配置变量
REMOTE_USER="josie"
REMOTE_HOST="jo.mitrecx.top"
REMOTE_PATH="/home/josie/apps/family-bills-backend"
LOCAL_PATH="."

echo "1. 压缩本地文件..."
tar -czf family-bills-backend.tar.gz \
    --exclude=__pycache__ \
    --exclude=.git \
    --exclude=*.pyc \
    --exclude=.pytest_cache \
    --exclude=logs \
    --exclude=uploads \
    --exclude=*.log \
    --no-xattrs \
    .

echo "2. 上传文件到服务器..."
scp family-bills-backend.tar.gz ${REMOTE_USER}@${REMOTE_HOST}:~/

echo "3. 在远程服务器上部署..."
ssh ${REMOTE_USER}@${REMOTE_HOST} << EOF
    # 创建应用目录
    mkdir -p /home/josie/apps/family-bills-backend
    cd /home/josie/apps
    
    # 备份旧版本（如果存在）
    if [ -d "family-bills-backend-backup" ]; then
        rm -rf family-bills-backend-backup
    fi
    if [ -d "family-bills-backend" ]; then
        mv family-bills-backend family-bills-backend-backup
        mkdir -p family-bills-backend
    fi
    
    # 解压新版本
    cd family-bills-backend
    tar -xzf ~/family-bills-backend.tar.gz
    
    # 设置环境变量
    cat > .env << 'ENVEOF'
ENVIRONMENT=production
DATABASE_URL=postgresql://josie:bills_password_2024@localhost:5432/bills_db
SECRET_KEY=family-bills-production-secret-key-2024-very-long-and-secure
DEBUG=false
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://jo.mitrecx.top:3000,https://jo.mitrecx.top:3000,http://jo.mitrecx.top,https://jo.mitrecx.top
LOG_LEVEL=INFO
LOG_FILE=logs/production.log
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256
ENVEOF
    
    # 创建必要目录
    mkdir -p logs uploads
    
    # 智能安装Python依赖
    INSTALL_DEPS=false
    
    if [ "${FORCE_DEPS}" = "true" ]; then
        echo "强制重新安装依赖..."
        INSTALL_DEPS=true
    elif [ "${SKIP_DEPS}" = "true" ]; then
        echo "跳过依赖安装..."
        INSTALL_DEPS=false
    else
        # 智能检测是否需要安装依赖
        if [ ! -f ".deps_installed" ] || [ "requirements.txt" -nt ".deps_installed" ]; then
            echo "检测到依赖变化或首次部署，安装依赖..."
            INSTALL_DEPS=true
        else
            echo "依赖已是最新，跳过安装..."
            INSTALL_DEPS=false
        fi
    fi
    
    if [ "\$INSTALL_DEPS" = "true" ]; then
        echo "正在安装Python依赖..."
        pip3 install -r requirements.txt
        # 创建依赖安装标记文件
        touch .deps_installed
        echo "依赖安装完成"
    fi
    
    # 停止旧的服务（如果在运行）
    echo "停止旧服务..."
    # 更精确地停止服务
    pkill -f "python3 run.py" || true
    pkill -f "uvicorn.*main:app" || true
    # 等待进程完全停止
    sleep 3
    
    # 检查端口是否被占用，如果是则强制释放
    if lsof -ti:8000 > /dev/null 2>&1; then
        echo "端口8000仍被占用，强制释放..."
        lsof -ti:8000 | xargs kill -9 || true
        sleep 2
    fi
    
    # 启动新服务
    echo "启动新服务..."
    nohup python3 run.py > logs/app.log 2>&1 &
    
    # 等待服务启动
    sleep 5
    
    # 检查服务状态
    if curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo "✅ 服务启动成功！"
        echo "健康检查: http://jo.mitrecx.top:8000/api/v1/health"
        echo "API文档: http://jo.mitrecx.top:8000/docs"
    else
        echo "❌ 服务启动失败，请检查日志"
        tail -n 20 logs/app.log
        exit 1
    fi
    
    # 清理上传的压缩包
    rm -f ~/family-bills-backend.tar.gz
EOF

echo "4. 清理本地临时文件..."
rm -f family-bills-backend.tar.gz

echo "✅ 部署完成！"
echo "服务地址: http://jo.mitrecx.top:8000"
echo "健康检查: http://jo.mitrecx.top:8000/api/v1/health"
echo "API文档: http://jo.mitrecx.top:8000/docs"