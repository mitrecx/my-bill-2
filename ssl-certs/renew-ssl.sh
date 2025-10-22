#!/bin/bash

# SSL证书申请脚本
# 使用 Let's Encrypt 申请免费SSL证书
# 域名: bill.mitrecx.top

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置变量
DOMAIN="bill.mitrecx.top"
EMAIL="your-email@example.com"  # 请替换为你的邮箱
WEBROOT="/var/www/family-bills-frontend"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        log_info "请使用: sudo $0"
        exit 1
    fi
}

# 安装certbot
install_certbot() {
    log_info "检查并安装certbot..."
    
    if command -v certbot &> /dev/null; then
        log_success "certbot已安装"
        return
    fi
    
    # 根据系统类型安装certbot
    if command -v yum &> /dev/null; then
        # CentOS/RHEL
        yum install -y epel-release
        yum install -y certbot python3-certbot-nginx
    elif command -v apt &> /dev/null; then
        # Ubuntu/Debian
        apt update
        apt install -y certbot python3-certbot-nginx
    else
        log_error "不支持的操作系统"
        exit 1
    fi
    
    log_success "certbot安装完成"
}

# 申请SSL证书
request_certificate() {
    log_info "申请SSL证书..."
    
    # 使用webroot方式申请证书
    certbot certonly \
        --webroot \
        --webroot-path="$WEBROOT" \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --domains "$DOMAIN" \
        --non-interactive
    
    if [[ $? -eq 0 ]]; then
        log_success "SSL证书申请成功"
    else
        log_error "SSL证书申请失败"
        exit 1
    fi
}

# 配置nginx使用新证书
configure_nginx() {
    log_info "配置nginx使用新证书..."
    
    # 证书文件路径
    CERT_PATH="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
    KEY_PATH="/etc/letsencrypt/live/$DOMAIN/privkey.pem"
    
    # 检查证书文件是否存在
    if [[ ! -f "$CERT_PATH" ]] || [[ ! -f "$KEY_PATH" ]]; then
        log_error "证书文件不存在"
        exit 1
    fi
    
    # 复制证书到nginx目录
    mkdir -p /etc/nginx/ssl
    cp "$CERT_PATH" "/etc/nginx/ssl/$DOMAIN.pem"
    cp "$KEY_PATH" "/etc/nginx/ssl/$DOMAIN.key"
    
    # 设置权限
    chmod 644 "/etc/nginx/ssl/$DOMAIN.pem"
    chmod 600 "/etc/nginx/ssl/$DOMAIN.key"
    chown root:root "/etc/nginx/ssl/$DOMAIN.pem" "/etc/nginx/ssl/$DOMAIN.key"
    
    log_success "证书文件已复制到nginx目录"
}

# 恢复HTTPS配置
restore_https_config() {
    log_info "恢复HTTPS配置..."
    
    # 恢复原始的HTTPS配置
    cat > /etc/nginx/conf.d/family-bills.conf << 'EOF'
server {
    listen 443 ssl http2;
    server_name bill.mitrecx.top;

    ssl_certificate     /etc/nginx/ssl/bill.mitrecx.top.pem;
    ssl_certificate_key /etc/nginx/ssl/bill.mitrecx.top.key;
    
    # SSL 优化配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    root /var/www/family-bills-frontend;
    index index.html;
    
    # 前端路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API代理到后端
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
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

server {
    listen 80;
    server_name bill.mitrecx.top;
    return 301 https://$host$request_uri;
}
EOF
    
    log_success "HTTPS配置已恢复"
}

# 测试并重载nginx
reload_nginx() {
    log_info "测试nginx配置..."
    
    if nginx -t; then
        log_success "nginx配置测试通过"
        systemctl reload nginx
        log_success "nginx已重载"
    else
        log_error "nginx配置测试失败"
        exit 1
    fi
}

# 设置自动续期
setup_auto_renewal() {
    log_info "设置SSL证书自动续期..."
    
    # 添加cron任务
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet --post-hook 'systemctl reload nginx'") | crontab -
    
    log_success "自动续期已设置"
}

# 主函数
main() {
    log_info "开始申请SSL证书..."
    
    check_root
    install_certbot
    request_certificate
    configure_nginx
    restore_https_config
    reload_nginx
    setup_auto_renewal
    
    log_success "SSL证书申请和配置完成！"
    log_info "网站现在可以通过 https://$DOMAIN 安全访问"
    log_info "证书将自动续期"
}

# 运行主函数
main "$@"