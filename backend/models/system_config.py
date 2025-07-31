from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from config.database import Base


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, index=True, nullable=False, comment="配置键")
    config_value = Column(Text, nullable=True, comment="配置值")
    config_type = Column(String(20), nullable=False, default="string", comment="配置类型: string, int, bool, json")
    description = Column(String(255), nullable=True, comment="配置描述")
    is_encrypted = Column(Boolean, default=False, comment="是否加密存储")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<SystemConfig(key={self.config_key}, value={self.config_value})>"