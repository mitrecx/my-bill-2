from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
import logging

from config.database import get_db
from models.family import Family, FamilyMember
from models.user import User
from api.auth import get_current_user
from schemas.family import (
    FamilyCreate,
    FamilyUpdate,
    FamilyResponse,
    FamilyWithMembersResponse,
    FamilyMemberResponse,
    ApiResponse,  # 新增导入
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/families", tags=["families"])


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
    family_in: FamilyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建家庭，并将当前用户设为管理员"""
    try:
        family = Family(
            family_name=family_in.family_name,
            description=family_in.description,
            created_by=current_user.id,
        )
        db.add(family)
        db.commit()
        db.refresh(family)

        member = FamilyMember(
            family_id=family.id,
            user_id=current_user.id,
            role="admin",
        )
        db.add(member)
        db.commit()

        return family
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