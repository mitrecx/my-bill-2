from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SystemConfigBase(BaseModel):
    """系统配置基础模型"""
    config_key: str = Field(..., description="配置键")
    config_value: Optional[str] = Field(None, description="配置值")
    config_type: str = Field(default="string", description="配置类型")
    description: Optional[str] = Field(None, description="配置描述")
    is_encrypted: bool = Field(default=False, description="是否加密存储")


class SystemConfigCreate(SystemConfigBase):
    """创建系统配置"""
    pass


class SystemConfigUpdate(BaseModel):
    """更新系统配置"""
    config_value: Optional[str] = Field(None, description="配置值")
    description: Optional[str] = Field(None, description="配置描述")


class SystemConfigResponse(SystemConfigBase):
    """系统配置响应"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DefaultPasswordConfig(BaseModel):
    """默认密码配置"""
    default_password: str = Field(..., min_length=6, description="默认密码，至少6位")


class SystemConfigBatch(BaseModel):
    """批量配置更新"""
    configs: dict = Field(..., description="配置键值对")