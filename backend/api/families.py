from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from config.database import get_db
from models.user import User
from models.family import Family, FamilyMember
from schemas.family import FamilyResponse, FamilyCreate, FamilyUpdate, FamilyMemberResponse
from schemas.common import ApiResponse
from schemas.user import UserResponse
from api.auth import get_current_user
from services.family_service import FamilyService  # 导入服务

router = APIRouter(prefix="/families", tags=["families"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=ApiResponse[FamilyResponse])
async def create_family(
    family_in: FamilyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建家庭"""
    try:
        family_service = FamilyService(db)
        # 假设服务方法需要创建者ID
        new_family = family_service.create_family(
            family_data=family_in, creator_id=current_user.id
        )
        return ApiResponse(data=new_family, message="家庭创建成功")
    except Exception as e:
        logger.error(f"创建家庭失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{family_id}", response_model=ApiResponse[FamilyResponse])
async def update_family(
    family_id: int,
    family_in: FamilyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新家庭信息"""
    family_service = FamilyService(db)
    updated_family = family_service.update_family(
        family_id=family_id, family_data=family_in, user_id=current_user.id
    )
    if not updated_family:
        raise HTTPException(status_code=404, detail="家庭不存在或无权限")
    return ApiResponse(data=updated_family, message="家庭信息更新成功")


@router.delete("/{family_id}", response_model=ApiResponse[str])
async def delete_family(
    family_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除家庭"""
    family_service = FamilyService(db)
    if not family_service.delete_family(family_id=family_id, user_id=current_user.id):
        raise HTTPException(status_code=404, detail="家庭不存在或无权限")
    return ApiResponse(data="家庭已删除", message="家庭删除成功")


@router.get("/{family_id}/members", response_model=ApiResponse[List[FamilyMemberResponse]])
async def list_family_members(
    family_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取家庭成员列表"""
    family_service = FamilyService(db)
    members = family_service.get_family_members(
        family_id=family_id, user_id=current_user.id
    )
    if members is None:
        raise HTTPException(status_code=404, detail="家庭不存在或无权限")
    
    # 手动构建响应以匹配 `FamilyMemberResponse`
    member_responses = [
        FamilyMemberResponse(
            id=member.id,
            user_id=member.user_id,
            role=member.role,
            joined_at=member.joined_at,
            user=(
                UserResponse(
                    id=member.user.id,
                    username=member.user.username,
                    full_name=member.user.full_name,
                    email=member.user.email,
                    is_active=member.user.is_active,
                    is_admin=member.user.is_admin,
                    created_at=member.user.created_at,
                    family_name=None,
                    family_role=member.role,
                ) if member.user else None
            ),
        )
        for member in members
    ]
    return ApiResponse(data=member_responses, message="获取家庭成员成功")


@router.get("", response_model=ApiResponse[List[FamilyResponse]])
async def get_user_families(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户所属的家庭列表"""
    family_service = FamilyService(db)
    families = family_service.get_user_families(user_id=current_user.id)
    return ApiResponse(success=True, data=families, message="获取家庭列表成功")