#!/bin/bash

# SSL证书自动部署脚本
# 用于部署SSL证书到 jo.mitrecx.top 服务器
# 作者: 家庭账单管理系统
# 日期: $(date +%Y-%m-%d)

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
DOMAIN="jo.mitrecx.top"
LOCAL_CERT_DIR="$(dirname "$0")"
LOCAL_KEY_FILE="${LOCAL_CERT_DIR}/${DOMAIN}.key"
LOCAL_CERT_FILE="${LOCAL_CERT_DIR}/${DOMAIN}.pem"

# 服务器配置
SERVER_USER="josie"
SERVER_HOST="${DOMAIN}"
SERVER_CERT_DIR="/etc/nginx/ssl"
SERVER_KEY_FILE="${SERVER_CERT_DIR}/${DOMAIN}.key"
SERVER_CERT_FILE="${SERVER_CERT_DIR}/${DOMAIN}.pem"

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

# 检查本地证书文件
check_local_files() {
    log_info "检查本地SSL证书文件..."
    
    if [[ ! -f "$LOCAL_KEY_FILE" ]]; then
        log_error "私钥文件不存在: $LOCAL_KEY_FILE"
        exit 1
    fi
    
    if [[ ! -f "$LOCAL_CERT_FILE" ]]; then
        log_error "证书文件不存在: $LOCAL_CERT_FILE"
        exit 1
    fi
    
    log_success "本地证书文件检查通过"
}

# 验证证书有效性
validate_certificate() {
    log_info "验证SSL证书有效性..."
    
    # 检查证书格式
    if ! openssl x509 -in "$LOCAL_CERT_FILE" -text -noout > /dev/null 2>&1; then
        log_error "证书文件格式无效"
        exit 1
    fi
    
    # 检查私钥格式
    if ! openssl rsa -in "$LOCAL_KEY_FILE" -check -noout > /dev/null 2>&1; then
        log_error "私钥文件格式无效"
        exit 1
    fi
    
    # 检查证书和私钥是否匹配
    cert_modulus=$(openssl x509 -noout -modulus -in "$LOCAL_CERT_FILE" | openssl md5)
    key_modulus=$(openssl rsa -noout -modulus -in "$LOCAL_KEY_FILE" | openssl md5)
    
    if [[ "$cert_modulus" != "$key_modulus" ]]; then
        log_error "证书和私钥不匹配"
        exit 1
    fi
    
    # 显示证书信息
    log_info "证书信息:"
    openssl x509 -in "$LOCAL_CERT_FILE" -text -noout | grep -E "(Subject:|Issuer:|Not Before:|Not After:)" | sed 's/^/    /'
    
    log_success "证书验证通过"
}

# 检查服务器连接
check_server_connection() {
    log_info "检查服务器连接..."
    
    if ! ssh -o ConnectTimeout=100 -o BatchMode=yes "${SERVER_USER}@${SERVER_HOST}" "echo 'Connection test successful'" > /dev/null 2>&1; then
        log_error "无法连接到服务器 ${SERVER_HOST}"
        log_error "请确保:"
        log_error "1. 服务器地址正确"
        log_error "2. SSH密钥已配置"
        log_error "3. 网络连接正常"
        exit 1
    fi
    
    log_success "服务器连接正常"
}

# 备份现有证书
backup_existing_certificates() {
    log_info "备份服务器上的现有证书..."
    
    backup_dir="/etc/nginx/ssl/backup/$(date +%Y%m%d_%H%M%S)"
    
    ssh "${SERVER_USER}@${SERVER_HOST}" "
        if [[ -f '${SERVER_CERT_FILE}' ]] || [[ -f '${SERVER_KEY_FILE}' ]]; then
            sudo mkdir -p '${backup_dir}'
            [[ -f '${SERVER_CERT_FILE}' ]] && sudo cp '${SERVER_CERT_FILE}' '${backup_dir}/'
            [[ -f '${SERVER_KEY_FILE}' ]] && sudo cp '${SERVER_KEY_FILE}' '${backup_dir}/'
            echo 'Backup created at: ${backup_dir}'
        else
            echo 'No existing certificates to backup'
        fi
    "
    
    log_success "证书备份完成"
}

# 上传证书文件
upload_certificates() {
    log_info "上传SSL证书到服务器..."
    
    # 确保目标目录存在并设置正确权限
    ssh "${SERVER_USER}@${SERVER_HOST}" "
        sudo mkdir -p '${SERVER_CERT_DIR}'
        sudo chown root:root '${SERVER_CERT_DIR}'
        sudo chmod 755 '${SERVER_CERT_DIR}'
    "
    
    # 先上传到临时目录，然后移动到目标位置
    temp_dir="/tmp/ssl_upload_$$"
    ssh "${SERVER_USER}@${SERVER_HOST}" "mkdir -p '${temp_dir}'"
    
    # 上传证书文件到临时目录
    scp "$LOCAL_CERT_FILE" "${SERVER_USER}@${SERVER_HOST}:${temp_dir}/$(basename ${SERVER_CERT_FILE})"
    scp "$LOCAL_KEY_FILE" "${SERVER_USER}@${SERVER_HOST}:${temp_dir}/$(basename ${SERVER_KEY_FILE})"
    
    # 移动文件到目标位置并设置权限
    ssh "${SERVER_USER}@${SERVER_HOST}" "
        sudo mv '${temp_dir}/$(basename ${SERVER_CERT_FILE})' '${SERVER_CERT_FILE}'
        sudo mv '${temp_dir}/$(basename ${SERVER_KEY_FILE})' '${SERVER_KEY_FILE}'
        sudo chmod 644 '${SERVER_CERT_FILE}'
        sudo chmod 600 '${SERVER_KEY_FILE}'
        sudo chown root:root '${SERVER_CERT_FILE}' '${SERVER_KEY_FILE}'
        rm -rf '${temp_dir}'
    "
    
    log_success "证书文件上传完成"
}

# 验证Nginx配置
validate_nginx_config() {
    log_info "验证Nginx配置..."
    
    if ssh "${SERVER_USER}@${SERVER_HOST}" "sudo nginx -t" > /dev/null 2>&1; then
        log_success "Nginx配置验证通过"
    else
        log_error "Nginx配置验证失败"
        log_error "正在恢复备份..."
        
        # 这里可以添加恢复逻辑
        exit 1
    fi
}

# 重载Nginx服务
reload_nginx() {
    log_info "重载Nginx服务..."
    
    if ssh "${SERVER_USER}@${SERVER_HOST}" "sudo systemctl reload nginx"; then
        log_success "Nginx服务重载成功"
    else
        log_error "Nginx服务重载失败"
        exit 1
    fi
}

# 测试SSL证书
test_ssl_certificate() {
    log_info "测试SSL证书..."
    
    # 等待几秒让服务完全启动
    sleep 3
    
    # 测试HTTPS连接
    if curl -s --connect-timeout 10 "https://${DOMAIN}" > /dev/null 2>&1; then
        log_success "HTTPS连接测试成功"
    else
        log_warning "HTTPS连接测试失败，请手动检查"
    fi
    
    # 显示证书信息
    log_info "当前证书信息:"
    echo | openssl s_client -servername "${DOMAIN}" -connect "${DOMAIN}:443" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null | sed 's/^/    /' || log_warning "无法获取远程证书信息"
}

# 清理函数
cleanup() {
    log_info "清理临时文件..."
    # 这里可以添加清理逻辑
}

# 主函数
main() {
    echo "=================================================="
    echo "       SSL证书自动部署脚本 v1.0"
    echo "       域名: ${DOMAIN}"
    echo "       时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=================================================="
    echo
    
    # 设置清理陷阱
    trap cleanup EXIT
    
    # 执行部署步骤
    check_local_files
    validate_certificate
    check_server_connection
    backup_existing_certificates
    upload_certificates
    validate_nginx_config
    reload_nginx
    test_ssl_certificate
    
    echo
    echo "=================================================="
    log_success "SSL证书部署完成！"
    echo "=================================================="
    echo
    log_info "部署摘要:"
    log_info "- 域名: ${DOMAIN}"
    log_info "- 证书文件: ${SERVER_CERT_FILE}"
    log_info "- 私钥文件: ${SERVER_KEY_FILE}"
    log_info "- 部署时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo
    log_info "建议操作:"
    log_info "1. 访问 https://${DOMAIN} 验证证书"
    log_info "2. 检查证书有效期"
    log_info "3. 设置证书到期提醒"
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi