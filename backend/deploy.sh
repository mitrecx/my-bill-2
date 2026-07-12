#!/bin/bash

# 后端服务部署脚本
# 部署配置见仓库根目录 .env.deploy（参考 .env.deploy.example）
# 使用方法:
#   ./deploy.sh              # 正常部署，智能检测是否需要安装依赖
#   ./deploy.sh --deps       # 强制重新安装依赖
#   ./deploy.sh --no-deps    # 跳过依赖安装
#   ./deploy.sh restart      # 重启 systemd 服务
#   ./deploy.sh status       # 查看服务状态
#   ./deploy.sh logs         # 跟踪 journalctl 日志
#   ./deploy.sh stop         # 停止服务

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../scripts/load-deploy-env.sh
source "${SCRIPT_DIR}/../scripts/load-deploy-env.sh"

REMOTE_USER="${DEPLOY_REMOTE_USER}"
REMOTE_HOST="${DEPLOY_REMOTE_HOST}"
REMOTE_PATH="${DEPLOY_BACKEND_REMOTE_PATH}"
SERVICE_NAME="${DEPLOY_SERVICE_NAME}"
PUBLIC_URL="${DEPLOY_PUBLIC_URL}"
PUBLIC_HOST="${DEPLOY_PUBLIC_HOST}"
LOCAL_PATH="."

# 解析命令行参数
FORCE_DEPS=false
SKIP_DEPS=false
COMMAND="deploy"

for arg in "$@"; do
    case $arg in
        --deps)
            FORCE_DEPS=true
            ;;
        --no-deps)
            SKIP_DEPS=true
            ;;
        deploy|restart|status|logs|stop)
            COMMAND=$arg
            ;;
        *)
            echo "未知参数: $arg"
            echo "使用方法: $0 [deploy] [--deps|--no-deps] | restart | status | logs | stop"
            exit 1
            ;;
    esac
done

sync_systemd_unit_and_restart() {
    echo "同步 systemd 单元 (${SERVICE_NAME})..."
    scp "${SCRIPT_DIR}/deploy/${SERVICE_NAME}.service" "${REMOTE_USER}@${REMOTE_HOST}:/tmp/"

    ssh -T "${REMOTE_USER}@${REMOTE_HOST}" "SERVICE_NAME=${SERVICE_NAME}" <<'EOF'
        set -e
        LOADED=$(systemctl show -p LoadState --value "${SERVICE_NAME}.service" 2>/dev/null || echo "not-found")
        if [ "$LOADED" != "loaded" ]; then
            echo "  → 停止旧的 nohup 进程..."
            pkill -f "python3 run.py" || true
            pkill -f "uvicorn.*main:app" || true
            pkill -f "gunicorn.*main:app" || true
            sleep 2
            if lsof -ti:8000 > /dev/null 2>&1; then
                lsof -ti:8000 | xargs kill -9 || true
                sleep 1
            fi
        fi

        sudo cp "/tmp/${SERVICE_NAME}.service" "/etc/systemd/system/${SERVICE_NAME}.service"
        sudo systemctl daemon-reload
        sudo systemctl enable "${SERVICE_NAME}"
        sudo systemctl restart "${SERVICE_NAME}"
EOF
}

case "$COMMAND" in
    restart)
        echo "重启 ${SERVICE_NAME}..."
        ssh -T "${REMOTE_USER}@${REMOTE_HOST}" "sudo systemctl restart ${SERVICE_NAME}"
        echo "服务已重启。"
        exit 0
        ;;
    status)
        ssh -T "${REMOTE_USER}@${REMOTE_HOST}" "systemctl status ${SERVICE_NAME} --no-pager"
        exit 0
        ;;
    logs)
        ssh -T "${REMOTE_USER}@${REMOTE_HOST}" "journalctl -u ${SERVICE_NAME} -f"
        exit 0
        ;;
    stop)
        ssh -T "${REMOTE_USER}@${REMOTE_HOST}" "sudo systemctl stop ${SERVICE_NAME}"
        echo "服务已停止。"
        exit 0
        ;;
esac

echo "开始部署家庭账单管理系统后端服务..."

echo "1. 压缩本地文件..."
tar -czf family-bills-backend.tar.gz \
    --exclude=__pycache__ \
    --exclude=.git \
    --exclude=*.pyc \
    --exclude=.pytest_cache \
    --exclude=logs \
    --exclude=uploads \
    --exclude=*.log \
    --exclude=family-bills-backend.tar.gz \
    --no-xattrs \
    .

echo "2. 上传文件到服务器..."
scp family-bills-backend.tar.gz "${REMOTE_USER}@${REMOTE_HOST}:~/"

echo "3. 在远程服务器上部署..."
ssh -T "${REMOTE_USER}@${REMOTE_HOST}" "FORCE_DEPS=${FORCE_DEPS} SKIP_DEPS=${SKIP_DEPS} PUBLIC_HOST=${PUBLIC_HOST}" << 'EOF'
    set -e

    mkdir -p /home/josie/apps/family-bills-backend
    cd /home/josie/apps

    if [ -d "family-bills-backend-backup" ]; then
        rm -rf family-bills-backend-backup
    fi
    if [ -d "family-bills-backend" ]; then
        mv family-bills-backend family-bills-backend-backup
        mkdir -p family-bills-backend
    fi

    cd family-bills-backend
    tar -xzf ~/family-bills-backend.tar.gz

    if [ -f ../family-bills-backend-backup/.env ]; then
        cp ../family-bills-backend-backup/.env .env
    else
        cat > .env << 'ENVEOF'
ENVIRONMENT=production
DATABASE_URL=postgresql://josie:bills_password_2024@localhost:5432/bills_db
SECRET_KEY=family-bills-production-secret-key-2024-very-long-and-secure
DEBUG=false
HOST=127.0.0.1
PORT=8000
CORS_ORIGINS=http://${PUBLIC_HOST}:3000,https://${PUBLIC_HOST}:3000,http://${PUBLIC_HOST},https://${PUBLIC_HOST}
LOG_LEVEL=INFO
LOG_FILE=logs/production.log
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256
ENVEOF
    fi

    # 生产环境仅监听本机，由 nginx 反代
    if grep -q '^HOST=0.0.0.0' .env; then
        sed -i 's/^HOST=0.0.0.0/HOST=127.0.0.1/' .env
    fi

    mkdir -p logs uploads

    INSTALL_DEPS=false

    if [ "${FORCE_DEPS}" = "true" ]; then
        echo "强制重新安装依赖..."
        INSTALL_DEPS=true
    elif [ "${SKIP_DEPS}" = "true" ]; then
        echo "跳过依赖安装..."
        INSTALL_DEPS=false
    else
        if [ ! -f ".deps_installed" ] || [ "requirements.txt" -nt ".deps_installed" ]; then
            echo "检测到依赖变化或首次部署，安装依赖..."
            INSTALL_DEPS=true
        else
            echo "依赖已是最新，跳过安装..."
            INSTALL_DEPS=false
        fi
    fi

    if [ "$INSTALL_DEPS" = "true" ]; then
        echo "正在安装Python依赖..."
        pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/ --trusted-host pypi.tuna.tsinghua.edu.cn --timeout 300
        touch .deps_installed
        echo "依赖安装完成"
    fi
EOF

sync_systemd_unit_and_restart

echo "4. 健康检查..."
sleep 3
if ssh -T "${REMOTE_USER}@${REMOTE_HOST}" "curl -fsS http://127.0.0.1:8000/api/v1/health/ > /dev/null"; then
    echo "✅ 服务启动成功！"
    echo "健康检查: ${PUBLIC_URL}/api/v1/health/"
    echo "API文档: ${PUBLIC_URL}/api/docs"
else
    echo "❌ 服务启动失败，请检查日志:"
    ssh -T "${REMOTE_USER}@${REMOTE_HOST}" "journalctl -u ${SERVICE_NAME} -n 30 --no-pager"
    exit 1
fi

ssh -T "${REMOTE_USER}@${REMOTE_HOST}" "rm -f ~/family-bills-backend.tar.gz"

echo "5. 清理本地临时文件..."
rm -f family-bills-backend.tar.gz

echo "✅ 部署完成！"
echo "服务地址: ${PUBLIC_URL}"
echo "健康检查: ${PUBLIC_URL}/api/v1/health"
echo "API文档: ${PUBLIC_URL}/api/docs"
echo "查看日志: ./deploy.sh logs"
