import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator, Field
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    """应用配置"""
    
    # 基础配置
    PROJECT_NAME: str = "家庭账单管理系统"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "多用户家庭账单管理系统API"
    
    # 环境配置
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # 服务器配置
    HOST: str = Field(default="127.0.0.1", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # 安全配置
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # 数据库配置
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    
    # CORS配置
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://localhost:5174",
        description="允许的CORS源，逗号分隔",
        env="CORS_ORIGINS"
    )
    
    # 文件上传配置
    UPLOAD_DIR: str = Field(default="uploads", env="UPLOAD_DIR")
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    ALLOWED_EXTENSIONS: str = Field(default=".csv,.xlsx,.xls", env="ALLOWED_EXTENSIONS")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="logs/app.log", env="LOG_FILE")
    
    # Redis配置（可选）
    REDIS_URL: Optional[str] = Field(default=None, env="REDIS_URL")
    
    @validator('SECRET_KEY')
    def secret_key_must_be_strong(cls, v):
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters')
        return v
    
    @validator('ENVIRONMENT')
    def environment_must_be_valid(cls, v):
        valid_envs = ['development', 'production', 'testing']
        if v not in valid_envs:
            raise ValueError(f'ENVIRONMENT must be one of {valid_envs}')
        return v
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """解析CORS origins"""
        if isinstance(v, str):
            return v  # 保持字符串格式
        return v
    
    @property
    def cors_origins(self) -> List[str]:
        """获取CORS origins列表"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    @property
    def allowed_extensions(self) -> List[str]:
        """获取允许的文件扩展名列表"""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",") if ext.strip()]
    
    @property
    def max_file_size(self) -> int:
        """获取最大文件大小"""
        return self.MAX_FILE_SIZE
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "testing"
    
    @property
    def upload_path(self) -> Path:
        """上传文件路径"""
        path = BASE_DIR / self.UPLOAD_DIR
        path.mkdir(exist_ok=True)
        return path
    
    @property
    def log_path(self) -> Path:
        """日志文件路径"""
        path = BASE_DIR / self.LOG_FILE
        path.parent.mkdir(exist_ok=True)
        return path
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 根据环境加载特定配置
def get_settings() -> Settings:
    """获取配置实例"""
    env = os.getenv("ENVIRONMENT", "development")
    
    # 检查根目录是否有 .env 文件（部署时创建的）
    root_env_file = BASE_DIR / ".env"
    if root_env_file.exists():
        # 优先使用根目录的 .env 文件（部署配置）
        settings_instance = Settings(_env_file=str(root_env_file))
        
        # 如果HOST是系统架构信息，使用默认值
        if hasattr(settings_instance, 'HOST') and 'darwin' in settings_instance.HOST:
            # 重新从文件读取HOST配置
            from dotenv import dotenv_values
            env_vars = dotenv_values(root_env_file)
            if 'HOST' in env_vars:
                settings_instance.HOST = env_vars['HOST']
            else:
                settings_instance.HOST = "0.0.0.0" if env == "production" else "127.0.0.1"
        
        return settings_instance
    
    # 如果没有根目录 .env 文件，尝试加载环境特定的配置文件
    env_file_path = BASE_DIR / "config" / "environments" / f"{env}.env"
    if env_file_path.exists():
        settings_instance = Settings(_env_file=str(env_file_path))
        
        # 如果HOST是系统架构信息，使用默认值
        if hasattr(settings_instance, 'HOST') and 'darwin' in settings_instance.HOST:
            from dotenv import dotenv_values
            env_vars = dotenv_values(env_file_path)
            if 'HOST' in env_vars:
                settings_instance.HOST = env_vars['HOST']
            else:
                settings_instance.HOST = "0.0.0.0" if env == "production" else "127.0.0.1"
        
        return settings_instance
    
    return Settings()


# 全局配置实例
settings = get_settings()