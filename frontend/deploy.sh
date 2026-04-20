#!/bin/bash

# 前端部署脚本
# 部署到 bill.mitrecx.top 服务器
# 仅更新静态资源与 nginx reload，不覆盖 HTTPS / vhost 配置（避免误用过期证书副本）
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
REMOTE_HOST="bill.mitrecx.top"
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
# 注入生产环境变量，确保前端指向生产API
VITE_USE_PROD_API=true npm run build

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
    
    # 重要：不再用脚本覆盖 /etc/nginx/conf.d/*.conf。
    # 旧逻辑每次部署都会写入固定路径 ssl_certificate /etc/nginx/ssl/bill.mitrecx.top.pem；
    # 若线上实际使用 Let's Encrypt（/etc/letsencrypt/live/...）或定期更新的证书，
    # 覆盖后 Nginx 会改指向可能过期的 /etc/nginx/ssl/ 副本，表现为「一部署证书就过期」。
    # HTTPS / 反代 / 证书路径请在服务器上单独维护（见仓库 ssl-certs/、family-bills-https.conf）。
    
    # 仅校验并重载，使静态文件更新生效（不修改 vhost / 证书）
    sudo nginx -t
    sudo systemctl reload nginx
    
    # 检查nginx状态
    if sudo systemctl is-active --quiet nginx; then
        echo "✅ Nginx重新加载成功！"
        echo "前端地址: https://bill.mitrecx.top"
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
echo "网站地址: https://bill.mitrecx.top"
echo "API地址: https://bill.mitrecx.top/api"
echo "后端文档: https://bill.mitrecx.top/api/docs"