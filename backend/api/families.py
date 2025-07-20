from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import logging

from config.database import get_db
from models.family import Family, FamilyMember
from models.user import User
from api.auth import get_current_user
from services.family_service import FamilyService
from schemas.family import (
    FamilyCreate,
    FamilyUpdate,
    FamilyResponse,
    FamilyWithMembersResponse,
    FamilyMemberResponse,
    ApiResponse,  # 新增导入
)
from schemas.common import ApiResponse as CommonApiResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/families", tags=["families"])


class FamilyCreateWithInvites(FamilyCreate):
    invite_usernames: Optional[List[str]] = []


class UserSearchResponse(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    
    class Config:
        from_attributes = True


@router.get("/search-users", response_model=CommonApiResponse[List[UserSearchResponse]])
async def search_users(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """搜索用户（用于邀请）"""
    family_service = FamilyService(db)
    users = family_service.search_users(q, exclude_user_id=current_user.id)
    
    return CommonApiResponse(
        data=[UserSearchResponse.model_validate(user) for user in users]
    )


@router.get("/", response_model=ApiResponse)
async def list_families(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户所属家庭列表"""
    try:
        families = (
            db.query(Family)
            .join(FamilyMember, Family.id == FamilyMember.family_id)
            .filter(FamilyMember.user_id == current_user.id)
            .all()
        )
        return {"data": families, "success": True, "message": "获取成功"}
    except Exception as e:
        logger.error(f"获取家庭列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取家庭列表失败")


@router.post("/", response_model=FamilyResponse)
async def create_family(
    family_in: FamilyCreateWithInvites,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建家庭，并将当前用户设为管理员，可选择邀请成员"""
    try:
        family_service = FamilyService(db)
        
        # 检查用户是否已在其他家庭中
        existing_family = family_service.get_user_family(current_user.id)
        if existing_family:
            raise HTTPException(status_code=400, detail="你已经在其他家庭中")
        
        # 创建家庭并发送邀请
        family_data = FamilyCreate(
            family_name=family_in.family_name,
            description=family_in.description
        )
        
        family = family_service.create_family_with_invites(
            family_data=family_data,
            creator_id=current_user.id,
            invite_usernames=family_in.invite_usernames
        )

        return family
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"创建家庭失败: {e}")
        raise HTTPException(status_code=500, detail="创建家庭失败")


@router.put("/{family_id}", response_model=FamilyResponse)
async def update_family(
    family_id: int,
    family_in: FamilyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新家庭信息（仅管理员）"""
    fam: Family = db.query(Family).filter(Family.id == family_id).first()
    if not fam:
        raise HTTPException(status_code=404, detail="家庭不存在")

    # 检查权限
    member: FamilyMember = (
        db.query(FamilyMember)
        .filter(FamilyMember.family_id == family_id, FamilyMember.user_id == current_user.id)
        .first()
    )
    if not member or member.role != "admin":
        raise HTTPException(status_code=403, detail="无权限")

    if family_in.family_name is not None:
        fam.family_name = family_in.family_name
    if family_in.description is not None:
        fam.description = family_in.description

    db.commit()
    db.refresh(fam)
    return fam


@router.delete("/{family_id}")
async def delete_family(
    family_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除家庭（仅管理员）"""
    fam: Family = db.query(Family).filter(Family.id == family_id).first()
    if not fam:
        raise HTTPException(status_code=404, detail="家庭不存在")

    member: FamilyMember = (
        db.query(FamilyMember)
        .filter(FamilyMember.family_id == family_id, FamilyMember.user_id == current_user.id)
        .first()
    )
    if not member or member.role != "admin":
        raise HTTPException(status_code=403, detail="无权限")

    db.delete(fam)
    db.commit()
    return {"detail": "家庭已删除"}


@router.get("/{family_id}/members", response_model=List[FamilyMemberResponse])
async def list_family_members(
    family_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    fam = db.query(Family).filter(Family.id == family_id).first()
    if not fam:
        raise HTTPException(status_code=404, detail="家庭不存在")

    member = (
        db.query(FamilyMember)
        .filter(FamilyMember.family_id == family_id, FamilyMember.user_id == current_user.id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=403, detail="无权限")

    members = db.query(FamilyMember).filter(FamilyMember.family_id == family_id).all()
    return members


@router.delete("/{family_id}/leave", response_model=CommonApiResponse[str])
async def leave_family(
    family_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """退出家庭"""
    try:
        family_service = FamilyService(db)
        
        # 检查用户是否在该家庭中
        member = db.query(FamilyMember).filter(
            FamilyMember.family_id == family_id,
            FamilyMember.user_id == current_user.id
        ).first()
        
        if not member:
            raise HTTPException(status_code=404, detail="你不在该家庭中")
        
        # 检查是否为管理员
        if member.role == "admin":
            # 检查是否还有其他成员
            other_members = db.query(FamilyMember).filter(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id != current_user.id
            ).count()
            
            if other_members > 0:
                raise HTTPException(
                    status_code=400, 
                    detail="作为管理员，你需要先转让管理权限或删除家庭"
                )
        
        # 移除成员
        family_service.remove_member_from_family(family_id, current_user.id)
        
        return CommonApiResponse(data="成功退出家庭")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"退出家庭失败: {e}")
        raise HTTPException(status_code=500, detail="退出家庭失败")