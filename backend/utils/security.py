from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from config.settings import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希值"""
    return pwd_context.hash(password)

# 为向后兼容提供 encrypt_password 别名

encrypt_password = get_password_hash


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """验证并解析令牌"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def refresh_token_if_needed(token: str) -> Tuple[Optional[str], bool]:
    """
    检查token是否需要刷新，如果需要则返回新token
    
    Args:
        token: 原始token
        
    Returns:
        Tuple[Optional[str], bool]: (新token或None, 是否刷新了token)
    """
    try:
        # 解析token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # 获取过期时间
        exp = payload.get("exp")
        if not exp:
            return None, False
            
        # 计算剩余时间
        exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        # 如果token已过期，返回None
        if now >= exp_datetime:
            return None, False
            
        # 创建新的token，重置过期时间为30分钟
        new_payload = payload.copy()
        # 移除旧的过期时间
        new_payload.pop("exp", None)
        
        # 创建新token
        new_token = create_access_token(
            data=new_payload,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return new_token, True
        
    except JWTError:
        return None, False


def validate_password_strength(password: str) -> tuple[bool, str]:
    """验证密码强度"""
    if len(password) < settings.password_min_length:
        return False, f"密码长度至少需要{settings.password_min_length}个字符"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, "密码必须包含大小写字母和数字"
    
    return True, "密码强度符合要求"