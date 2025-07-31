from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models.system_config import SystemConfig
from schemas.system_config import SystemConfigCreate, SystemConfigUpdate
from utils.security import encrypt_password, verify_password
import json


class SystemConfigService:
    """系统配置服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_config(self, config_key: str) -> Optional[SystemConfig]:
        """获取单个配置"""
        return self.db.query(SystemConfig).filter(
            SystemConfig.config_key == config_key
        ).first()
    
    def get_all_configs(self) -> List[SystemConfig]:
        """获取所有配置"""
        return self.db.query(SystemConfig).all()
    
    def get_configs_by_type(self, config_type: str) -> List[SystemConfig]:
        """根据类型获取配置"""
        return self.db.query(SystemConfig).filter(
            SystemConfig.config_type == config_type
        ).all()
    
    def create_config(self, config_data: SystemConfigCreate) -> SystemConfig:
        """创建配置"""
        # 检查配置键是否已存在
        existing = self.get_config(config_data.config_key)
        if existing:
            raise ValueError(f"配置键 '{config_data.config_key}' 已存在")
        
        # 处理加密
        config_value = config_data.config_value
        if config_data.is_encrypted and config_value:
            config_value = encrypt_password(config_value)
        
        db_config = SystemConfig(
            config_key=config_data.config_key,
            config_value=config_value,
            config_type=config_data.config_type,
            description=config_data.description,
            is_encrypted=config_data.is_encrypted
        )
        
        self.db.add(db_config)
        self.db.commit()
        self.db.refresh(db_config)
        return db_config
    
    def update_config(self, config_key: str, config_data: SystemConfigUpdate) -> Optional[SystemConfig]:
        """更新配置"""
        db_config = self.get_config(config_key)
        if not db_config:
            return None
        
        # 更新字段
        if config_data.config_value is not None:
            if db_config.is_encrypted:
                db_config.config_value = encrypt_password(config_data.config_value)
            else:
                db_config.config_value = config_data.config_value
        
        if config_data.description is not None:
            db_config.description = config_data.description
        
        self.db.commit()
        self.db.refresh(db_config)
        return db_config
    
    def delete_config(self, config_key: str) -> bool:
        """删除配置"""
        db_config = self.get_config(config_key)
        if not db_config:
            return False
        
        self.db.delete(db_config)
        self.db.commit()
        return True
    
    def get_config_value(self, config_key: str, default_value: Any = None) -> Any:
        """获取配置值，支持类型转换"""
        config = self.get_config(config_key)
        if not config or config.config_value is None:
            return default_value
        
        value = config.config_value
        
        # 根据类型转换
        if config.config_type == "int":
            try:
                return int(value)
            except (ValueError, TypeError):
                return default_value
        elif config.config_type == "bool":
            return value.lower() in ("true", "1", "yes", "on")
        elif config.config_type == "json":
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return default_value
        else:
            return value
    
    def set_config_value(self, config_key: str, value: Any, config_type: str = "string", 
                        description: str = None, is_encrypted: bool = False) -> SystemConfig:
        """设置配置值"""
        # 转换值为字符串
        if config_type == "json":
            str_value = json.dumps(value, ensure_ascii=False)
        elif config_type == "bool":
            str_value = "true" if value else "false"
        else:
            str_value = str(value)
        
        existing = self.get_config(config_key)
        if existing:
            # 更新现有配置
            update_data = SystemConfigUpdate(
                config_value=str_value,
                description=description
            )
            return self.update_config(config_key, update_data)
        else:
            # 创建新配置
            create_data = SystemConfigCreate(
                config_key=config_key,
                config_value=str_value,
                config_type=config_type,
                description=description,
                is_encrypted=is_encrypted
            )
            return self.create_config(create_data)
    
    def batch_update_configs(self, configs: Dict[str, Any]) -> List[SystemConfig]:
        """批量更新配置"""
        results = []
        for key, value in configs.items():
            try:
                config = self.set_config_value(key, value)
                results.append(config)
            except Exception as e:
                # 记录错误但继续处理其他配置
                print(f"更新配置 {key} 失败: {e}")
        
        return results
    
    def initialize_default_configs(self):
        """初始化默认配置"""
        default_configs = [
            {
                "config_key": "default_password",
                "config_value": "123456",
                "config_type": "string",
                "description": "新用户默认密码",
                "is_encrypted": True
            },
            {
                "config_key": "password_reset_enabled",
                "config_value": "true",
                "config_type": "bool",
                "description": "是否启用密码重置功能"
            },
            {
                "config_key": "max_login_attempts",
                "config_value": "5",
                "config_type": "int",
                "description": "最大登录尝试次数"
            }
        ]
        
        for config_data in default_configs:
            existing = self.get_config(config_data["config_key"])
            if not existing:
                create_data = SystemConfigCreate(**config_data)
                self.create_config(create_data)