from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # 基本配置
    PROJECT_NAME: str = "家庭账单管理系统"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "多用户家庭账单管理系统API"
    DEBUG: bool = False
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://josie:bills_password_2024@jo.mitrecx.top:5432/bills_db"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 文件上传配置
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    upload_dir: str = "uploads"
    allowed_extensions: list = [".csv", ".pdf"]
    
    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # 开发环境
        "http://localhost:4173",  # 预览环境
        "http://jo.mitrecx.top",  # 生产环境
    ]
    
    # 密码配置
    password_min_length: int = 8
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 创建全局设置实例
settings = Settings()

# 确保上传目录存在
os.makedirs(settings.upload_dir, exist_ok=True)