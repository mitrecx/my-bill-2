from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from config.database import get_db
from models.user import User
from schemas.common import ApiResponse
from schemas.system_config import (
    SystemConfigResponse, 
    SystemConfigCreate, 
    SystemConfigUpdate,
    DefaultPasswordConfig,
    SystemConfigBatch
)
from services.system_config_service import SystemConfigService
from api.auth import get_current_user

router = APIRouter(prefix="/system-config", tags=["系统配置"])


def check_admin_permission(current_user: User):
    """检查管理员权限"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )


@router.get("", response_model=ApiResponse[List[SystemConfigResponse]])
async def get_all_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有系统配置"""
    check_admin_permission(current_user)
    
    service = SystemConfigService(db)
    configs = service.get_all_configs()
    
    # 对于加密的配置，不返回实际值
    for config in configs:
        if config.is_encrypted:
            config.config_value = "***"
    
    return ApiResponse(data=configs, message="获取配置列表成功")


@router.get("/{config_key}", response_model=ApiResponse[SystemConfigResponse])
async def get_config(
    config_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个配置"""
    check_admin_permission(current_user)
    
    service = SystemConfigService(db)
    config = service.get_config(config_key)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    # 对于加密的配置，不返回实际值
    if config.is_encrypted:
        config.config_value = "***"
    
    return ApiResponse(data=config, message="获取配置成功")


@router.post("", response_model=ApiResponse[SystemConfigResponse])
async def create_config(
    config_data: SystemConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建配置"""
    check_admin_permission(current_user)
    
    service = SystemConfigService(db)
    
    try:
        config = service.create_config(config_data)
        return ApiResponse(data=config, message="配置创建成功")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{config_key}", response_model=ApiResponse[SystemConfigResponse])
async def update_config(
    config_key: str,
    config_data: SystemConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新配置"""
    check_admin_permission(current_user)
    
    service = SystemConfigService(db)
    config = service.update_config(config_key, config_data)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    return ApiResponse(data=config, message="配置更新成功")


@router.delete("/{config_key}", response_model=ApiResponse[bool])
async def delete_config(
    config_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除配置"""
    check_admin_permission(current_user)
    
    service = SystemConfigService(db)
    success = service.delete_config(config_key)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    return ApiResponse(data=True, message="配置删除成功")


@router.post("/batch", response_model=ApiResponse[List[SystemConfigResponse]])
async def batch_update_configs(
    batch_data: SystemConfigBatch,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量更新配置"""
    check_admin_permission(current_user)
    
    service = SystemConfigService(db)
    configs = service.batch_update_configs(batch_data.configs)
    
    return ApiResponse(data=configs, message="批量更新配置成功")


@router.put("/default-password", response_model=ApiResponse[SystemConfigResponse])
async def update_default_password(
    password_data: DefaultPasswordConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新默认密码"""
    check_admin_permission(current_user)
    
    service = SystemConfigService(db)
    config = service.set_config_value(
        config_key="default_password",
        value=password_data.default_password,
        config_type="string",
        description="新用户默认密码",
        is_encrypted=True
    )
    
    return ApiResponse(data=config, message="默认密码更新成功")


@router.get("/default-password/current", response_model=ApiResponse[str])
async def get_current_default_password(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前默认密码（仅显示掩码）"""
    check_admin_permission(current_user)
    
    service = SystemConfigService(db)
    config = service.get_config("default_password")
    
    if not config:
        return ApiResponse(data="未设置", message="获取默认密码成功")
    
    # 返回掩码
    return ApiResponse(data="******", message="获取默认密码成功")


@router.post("/initialize", response_model=ApiResponse[bool])
async def initialize_default_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """初始化默认配置"""
    check_admin_permission(current_user)
    
    service = SystemConfigService(db)
    service.initialize_default_configs()
    
    return ApiResponse(data=True, message="默认配置初始化成功")