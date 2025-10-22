#!/bin/bash

# 远程日志查看脚本
# 用于查看 bill.mitrecx.top 服务器上的各种日志

REMOTE_USER="josie"
REMOTE_HOST="bill.mitrecx.top"
APP_PATH="/home/josie/apps/family-bills-backend"

# 显示使用帮助
show_help() {
    echo "远程日志查看工具"
    echo ""
    echo "使用方法:"
    echo "  $0 [选项]"
    echo ""
    echo "选项:"
    echo "  app           查看应用日志 (实时)"
    echo "  app-tail      查看应用日志 (最后50行)"
    echo "  prod          查看生产日志 (实时)"
    echo "  prod-tail     查看生产日志 (最后50行)"
    echo "  nginx-access  查看nginx访问日志 (实时)"
    echo "  nginx-error   查看nginx错误日志 (实时)"
    echo "  nginx-tail    查看nginx错误日志 (最后50行)"
    echo "  all-tail      查看所有日志的最后几行"
    echo "  status        查看服务状态"
    echo "  help          显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 app        # 实时查看应用日志"
    echo "  $0 all-tail   # 查看所有日志摘要"
}

# 查看应用日志（实时）
view_app_logs() {
    echo "📱 查看应用日志 (实时)..."
    echo "按 Ctrl+C 退出"
    ssh ${REMOTE_USER}@${REMOTE_HOST} "tail -f ${APP_PATH}/logs/app.log"
}

# 查看应用日志（最后50行）
view_app_logs_tail() {
    echo "📱 应用日志 (最后50行):"
    ssh ${REMOTE_USER}@${REMOTE_HOST} "tail -n 50 ${APP_PATH}/logs/app.log"
}

# 查看生产日志（实时）
view_prod_logs() {
    echo "🏭 查看生产日志 (实时)..."
    echo "按 Ctrl+C 退出"
    ssh ${REMOTE_USER}@${REMOTE_HOST} "tail -f ${APP_PATH}/logs/production.log"
}

# 查看生产日志（最后50行）
view_prod_logs_tail() {
    echo "🏭 生产日志 (最后50行):"
    ssh ${REMOTE_USER}@${REMOTE_HOST} "tail -n 50 ${APP_PATH}/logs/production.log"
}

# 查看nginx访问日志（实时）
view_nginx_access() {
    echo "🌐 查看nginx访问日志 (实时)..."
    echo "按 Ctrl+C 退出"
    ssh ${REMOTE_USER}@${REMOTE_HOST} "sudo tail -f /var/log/nginx/access.log"
}

# 查看nginx错误日志（实时）
view_nginx_error() {
    echo "❌ 查看nginx错误日志 (实时)..."
    echo "按 Ctrl+C 退出"
    ssh ${REMOTE_USER}@${REMOTE_HOST} "sudo tail -f /var/log/nginx/error.log"
}

# 查看nginx错误日志（最后50行）
view_nginx_error_tail() {
    echo "❌ nginx错误日志 (最后50行):"
    ssh ${REMOTE_USER}@${REMOTE_HOST} "sudo tail -n 50 /var/log/nginx/error.log"
}

# 查看所有日志摘要
view_all_tail() {
    echo "📊 所有日志摘要:"
    echo ""
    
    echo "=== 应用日志 (最后10行) ==="
    ssh ${REMOTE_USER}@${REMOTE_HOST} "tail -n 10 ${APP_PATH}/logs/app.log 2>/dev/null || echo '应用日志文件不存在'"
    echo ""
    
    echo "=== 生产日志 (最后10行) ==="
    ssh ${REMOTE_USER}@${REMOTE_HOST} "tail -n 10 ${APP_PATH}/logs/production.log 2>/dev/null || echo '生产日志文件不存在'"
    echo ""
    
    echo "=== Nginx错误日志 (最后10行) ==="
    ssh ${REMOTE_USER}@${REMOTE_HOST} "sudo tail -n 10 /var/log/nginx/error.log 2>/dev/null || echo 'Nginx错误日志文件不存在'"
    echo ""
}

# 查看服务状态
view_status() {
    echo "🔍 服务状态检查:"
    echo ""
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} << 'EOF'
        echo "=== 后端服务进程 ==="
        ps aux | grep -E "(python3 run.py|uvicorn)" | grep -v grep || echo "未找到后端服务进程"
        echo ""
        
        echo "=== 端口占用情况 ==="
        echo "端口8000 (后端):"
        lsof -i:8000 2>/dev/null || echo "端口8000未被占用"
        echo ""
        echo "端口80 (HTTP):"
        sudo lsof -i:80 2>/dev/null || echo "端口80未被占用"
        echo ""
        echo "端口443 (HTTPS):"
        sudo lsof -i:443 2>/dev/null || echo "端口443未被占用"
        echo ""
        
        echo "=== Nginx状态 ==="
        sudo systemctl status nginx --no-pager -l
        echo ""
        
        echo "=== 磁盘空间 ==="
        df -h | grep -E "(Filesystem|/dev/)"
        echo ""
        
        echo "=== 内存使用 ==="
        free -h
EOF
}

# 主逻辑
case "${1:-help}" in
    "app")
        view_app_logs
        ;;
    "app-tail")
        view_app_logs_tail
        ;;
    "prod")
        view_prod_logs
        ;;
    "prod-tail")
        view_prod_logs_tail
        ;;
    "nginx-access")
        view_nginx_access
        ;;
    "nginx-error")
        view_nginx_error
        ;;
    "nginx-tail")
        view_nginx_error_tail
        ;;
    "all-tail")
        view_all_tail
        ;;
    "status")
        view_status
        ;;
    "help"|*)
        show_help
        ;;
esac