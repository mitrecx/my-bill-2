from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import Optional
import logging

from config.database import get_db
from models.user import User
from models.family import FamilyMember, Family
from schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from schemas.common import ApiResponse
from api.auth import get_password_hash, is_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=ApiResponse[UserListResponse])
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(is_admin),
    db: Session = Depends(get_db)
):
    """
    获取用户列表（分页），仅管理员可访问。
    """
    try:
        base_query = db.query(User)
        if search:
            search_filter = or_(
                User.username.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
            base_query = base_query.filter(search_filter)

        total = base_query.count()

        users_query = base_query.options(
            joinedload(User.family_memberships).joinedload(FamilyMember.family)
        ).order_by(User.id).offset((page - 1) * size).limit(size)
        
        users = users_query.all()
        
        user_responses = []
        for user in users:
            family_member = user.family_memberships[0] if user.family_memberships else None
            user_responses.append(UserResponse(
                id=user.id,
                username=user.username,
                full_name=user.full_name,
                email=user.email,
                is_active=user.is_active,
                created_at=user.created_at,
                family_name=family_member.family.family_name if family_member and family_member.family else None,
                family_role=family_member.role if family_member else None
            ))
        
        return ApiResponse(success=True, message="获取用户列表成功", data=UserListResponse(
            items=user_responses,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        ))
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取用户列表失败")


@router.post("", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    current_user: User = Depends(is_admin),
    db: Session = Depends(get_db)
):
    """
    创建新用户，仅管理员可访问。
    """
    try:
        if db.query(User).filter(User.username == user_in.username).first():
            raise HTTPException(status_code=400, detail="用户名已存在")
        if user_in.email and db.query(User).filter(User.email == user_in.email).first():
            raise HTTPException(status_code=400, detail="邮箱已存在")
        
        hashed_password = get_password_hash(user_in.password)
        new_user = User(
            username=user_in.username,
            password_hash=hashed_password,
            full_name=user_in.full_name,
            email=user_in.email
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        user_response = UserResponse(
            id=new_user.id,
            username=new_user.username,
            full_name=new_user.full_name,
            email=new_user.email,
            is_active=new_user.is_active,
            created_at=new_user.created_at,
            family_name=None,
            family_role=None
        )
        
        return ApiResponse(success=True, data=user_response, message="用户创建成功")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建用户失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="创建用户失败")


@router.put("/{user_id}", response_model=ApiResponse[UserResponse])
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(is_admin),
    db: Session = Depends(get_db)
):
    """
    更新用户信息，仅管理员可访问。
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
            
        if user_in.full_name is not None:
            user.full_name = user_in.full_name
        if user_in.email is not None:
            if user.email != user_in.email and db.query(User).filter(User.email == user_in.email).first():
                raise HTTPException(status_code=400, detail="该邮箱已被其他用户使用")
            user.email = user_in.email
        if user_in.password:
            user.password_hash = get_password_hash(user_in.password)
        if user_in.is_active is not None:
            user.is_active = user_in.is_active
            
        db.commit()
        db.refresh(user)

        # 查询用户的家庭信息以构建完整的响应
        family_member = db.query(FamilyMember).filter(FamilyMember.user_id == user.id).first()
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
            family_name=family_member.family.family_name if family_member and family_member.family else None,
            family_role=family_member.role if family_member else None
        )
        return ApiResponse(success=True, data=user_response, message="用户信息更新成功")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新用户 {user_id} 失败: {e}")
        raise HTTPException(status_code=500, detail="更新用户失败")


@router.delete("/{user_id}", response_model=ApiResponse[str])
async def delete_user(
    user_id: int,
    current_user: User = Depends(is_admin),
    db: Session = Depends(get_db)
):
    """
    删除用户，仅管理员可访问。
    """
    try:
        if current_user.id == user_id:
            raise HTTPException(status_code=400, detail="不能删除自己")

        user_to_delete = db.query(User).filter(User.id == user_id).first()
        if not user_to_delete:
            raise HTTPException(status_code=404, detail="用户不存在")

        db.delete(user_to_delete)
        db.commit()
        return ApiResponse(success=True, data=f"用户 {user_to_delete.username} 已成功删除", message="用户删除成功")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除用户 {user_id} 失败: {e}")
        raise HTTPException(status_code=500, detail="删除用户失败")


@router.get("/{user_id}", response_model=ApiResponse[UserResponse])
async def get_user(
    user_id: int,
    current_user: User = Depends(is_admin),
    db: Session = Depends(get_db)
):
    """
    获取单个用户详情，仅管理员可访问。
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        family_member = db.query(FamilyMember).filter(FamilyMember.user_id == user_id).first()
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
            family_name=family_member.family.family_name if family_member and family_member.family else None,
            family_role=family_member.role if family_member else None
        )
        return ApiResponse(success=True, data=user_response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户 {user_id} 失败: {e}")
        raise HTTPException(status_code=500, detail="获取用户失败")