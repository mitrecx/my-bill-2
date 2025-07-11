import re
from typing import Optional
from email_validator import validate_email, EmailNotValidError
from config.settings import settings


def validate_email_format(email: str) -> tuple[bool, str]:
    """验证邮箱格式"""
    try:
        validated_email = validate_email(email)
        return True, validated_email.email
    except EmailNotValidError as e:
        return False, str(e)


def validate_username(username: str) -> tuple[bool, str]:
    """验证用户名格式"""
    if len(username) < 3:
        return False, "用户名长度至少3个字符"
    
    if len(username) > 20:
        return False, "用户名长度不能超过20个字符"
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "用户名只能包含字母、数字、下划线和短横线"
    
    return True, "用户名格式正确"


def validate_file_extension(filename: str) -> tuple[bool, str]:
    """验证文件扩展名"""
    if not filename:
        return False, "文件名不能为空"
    
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
    allowed_exts = [ext.lstrip('.') for ext in settings.allowed_extensions]
    
    if file_ext not in allowed_exts:
        return False, f"文件格式不支持，支持的格式：{', '.join(settings.allowed_extensions)}"
    
    return True, "文件格式正确"


def validate_file_size(file_size: int) -> tuple[bool, str]:
    """验证文件大小"""
    if file_size > settings.max_file_size:
        max_size_mb = settings.max_file_size / (1024 * 1024)
        return False, f"文件大小不能超过{max_size_mb:.1f}MB"
    
    return True, "文件大小符合要求"


def detect_file_source_type(filename: str, content_preview: str = "") -> Optional[str]:
    """根据文件名和内容预览检测账单来源类型"""
    filename_lower = filename.lower()
    
    # 根据文件名判断
    if "支付宝" in filename or "alipay" in filename_lower or "cashbook_record" in filename_lower:
        return "alipay"
    elif "京东" in filename or "jd" in filename_lower or "京东交易流水" in filename:
        return "jd"
    elif "招商银行" in filename or "cmb" in filename_lower or "招商银行交易流水" in filename:
        return "cmb"
    
    # 根据内容预览判断
    if content_preview:
        if "记录时间,交易类型,收支,金额" in content_preview or "支付宝" in content_preview:
            return "alipay"
        elif "交易时间,商户名称,交易说明,金额" in content_preview or "京东" in content_preview:
            return "jd"
        elif "招商银行交易流水" in content_preview or "Transaction Statement" in content_preview:
            return "cmb"
    
    return None


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除危险字符"""
    # 移除路径分隔符和其他危险字符
    dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
    sanitized = filename
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '_')
    
    # 限制文件名长度
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        max_name_len = 255 - len(ext) - 1 if ext else 255
        sanitized = f"{name[:max_name_len]}.{ext}" if ext else name[:255]
    
    return sanitized 