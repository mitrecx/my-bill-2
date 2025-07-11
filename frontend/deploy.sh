#!/bin/bash

# 前端部署脚本
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

echo "开始部署家庭账单管理系统前端..."

# 配置变量
REMOTE_USER="josie"
REMOTE_HOST="jo.mitrecx.top"
REMOTE_PATH="/var/www/family-bills-frontend"
LOCAL_PATH="."

# 检查是否需要安装依赖
INSTALL_DEPS=false

if [ "$FORCE_DEPS" = "true" ]; then
    echo "强制重新安装依赖..."
    INSTALL_DEPS=true
elif [ "$SKIP_DEPS" = "true" ]; then
    echo "跳过依赖安装..."
    INSTALL_DEPS=false
else
    # 智能检测是否需要安装依赖
    if [ ! -f ".deps_installed" ] || [ "package.json" -nt ".deps_installed" ] || [ "package-lock.json" -nt ".deps_installed" ]; then
        echo "检测到依赖变化或首次部署，安装依赖..."
        INSTALL_DEPS=true
    else
        echo "依赖已是最新，跳过安装..."
        INSTALL_DEPS=false
    fi
fi

# 安装依赖（如果需要）
if [ "$INSTALL_DEPS" = "true" ]; then
    echo "1. 安装前端依赖..."
    npm install
    # 创建依赖安装标记文件
    touch .deps_installed
    echo "依赖安装完成"
else
    echo "1. 跳过依赖安装..."
fi

echo "2. 构建前端项目..."
npm run build

echo "3. 压缩构建文件..."
cd dist
tar -czf ../family-bills-frontend.tar.gz --no-xattrs .
cd ..

echo "4. 上传文件到服务器..."
scp family-bills-frontend.tar.gz ${REMOTE_USER}@${REMOTE_HOST}:~/

echo "5. 在远程服务器上部署..."
ssh ${REMOTE_USER}@${REMOTE_HOST} << EOF
    # 创建网站目录
    sudo mkdir -p ${REMOTE_PATH}
    
    # 备份旧版本（如果存在）
    if [ -d "${REMOTE_PATH}-backup" ]; then
        sudo rm -rf ${REMOTE_PATH}-backup
    fi
    if [ -d "${REMOTE_PATH}" ] && [ "\$(ls -A ${REMOTE_PATH})" ]; then
        sudo mv ${REMOTE_PATH} ${REMOTE_PATH}-backup
        sudo mkdir -p ${REMOTE_PATH}
    fi
    
    # 解压新版本
    cd ${REMOTE_PATH}
    sudo tar -xzf ~/family-bills-frontend.tar.gz
    
    # 设置权限
    sudo chown -R nginx:nginx ${REMOTE_PATH}
    sudo chmod -R 755 ${REMOTE_PATH}
    
    # 创建或更新nginx配置
    sudo tee /etc/nginx/conf.d/family-bills.conf > /dev/null << 'NGINXEOF'
server {
    listen 80;
    server_name jo.mitrecx.top;
    root ${REMOTE_PATH};
    index index.html;
    
    # 前端路由支持
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    # API代理到后端
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)\$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
NGINXEOF
    
    # 配置已直接写入conf.d目录，无需额外启用
    
    # 测试nginx配置
    sudo nginx -t
    
    # 重新加载nginx
    sudo systemctl reload nginx
    
    # 检查nginx状态
    if sudo systemctl is-active --quiet nginx; then
        echo "✅ Nginx重新加载成功！"
        echo "前端地址: http://jo.mitrecx.top"
    else
        echo "❌ Nginx重新加载失败，请检查配置"
        sudo systemctl status nginx
        exit 1
    fi
    
    # 清理上传的压缩包
    rm -f ~/family-bills-frontend.tar.gz
EOF

echo "6. 清理本地临时文件..."
rm -f family-bills-frontend.tar.gz

echo "✅ 前端部署完成！"
echo "网站地址: http://jo.mitrecx.top"
echo "API地址: http://jo.mitrecx.top/api"
echo "后端文档: http://jo.mitrecx.top/api/docs"