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
from api.auth import get_password_hash, is_admin, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"]) 

# --- Moved earlier to ensure static '/profile' routes match before '/{user_id}' dynamic routes ---
@router.get("/profile", response_model=ApiResponse[UserResponse])
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前登录用户的资料。
    """
    try:
        family_member = db.query(FamilyMember).filter(FamilyMember.user_id == current_user.id).first()
        user_response = UserResponse(
            id=current_user.id,
            username=current_user.username,
            full_name=current_user.full_name,
            email=current_user.email,
            is_active=current_user.is_active,
            is_admin=current_user.is_admin,
            created_at=current_user.created_at,
            family_name=family_member.family.family_name if family_member and family_member.family else None,
            family_role=family_member.role if family_member else None
        )
        return ApiResponse(success=True, data=user_response, message="获取个人资料成功")
    except Exception as e:
        logger.error(f"获取个人资料失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取个人资料失败")


@router.put("/profile", response_model=ApiResponse[UserResponse])
async def update_profile(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新当前登录用户的个人资料。
    允许更新: full_name, email, password；忽略 is_active。
    """
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 更新姓名
        if user_in.full_name is not None:
            user.full_name = user_in.full_name

        # 更新邮箱（需唯一）
        if user_in.email is not None:
            if user.email != user_in.email and db.query(User).filter(User.email == user_in.email).first():
                raise HTTPException(status_code=400, detail="该邮箱已被其他用户使用")
            user.email = user_in.email

        # 更新密码（如果提供）
        if user_in.password:
            user.password_hash = get_password_hash(user_in.password)

        # is_active 仅管理员可改，这里忽略

        db.commit()
        db.refresh(user)

        family_member = db.query(FamilyMember).filter(FamilyMember.user_id == user.id).first()
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at,
            family_name=family_member.family.family_name if family_member and family_member.family else None,
            family_role=family_member.role if family_member else None
        )
        return ApiResponse(success=True, data=user_response, message="个人资料更新成功")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新个人资料失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="更新个人资料失败")


@router.get("", response_model=ApiResponse[UserListResponse])
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    username: Optional[str] = Query(None, description="用户名搜索"),
    full_name: Optional[str] = Query(None, description="姓名搜索"),
    role: Optional[str] = Query(None, description="角色搜索 (admin/user)"),
    current_user: User = Depends(is_admin),
    db: Session = Depends(get_db)
):
    """
    获取用户列表（分页），仅管理员可访问。
    """
    try:
        base_query = db.query(User)
        
        # 兼容旧的search参数
        if search:
            search_filter = or_(
                User.username.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
            base_query = base_query.filter(search_filter)
        
        # 新的分别搜索参数
        if username:
            base_query = base_query.filter(User.username.ilike(f"%{username}%"))
        
        if full_name:
            base_query = base_query.filter(User.full_name.ilike(f"%{full_name}%"))
        
        if role:
            if role.lower() == 'admin':
                base_query = base_query.filter(User.is_admin == True)
            elif role.lower() == 'user':
                base_query = base_query.filter(User.is_admin == False)

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
                is_admin=user.is_admin,
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
            is_admin=new_user.is_admin,
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
            is_admin=user.is_admin,
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


# 注：下面原先定义的 '/profile' 路由已上移，为避免重复注册，这里进行注释处理
# @router.get("/profile", response_model=ApiResponse[UserResponse])
# async def get_profile(
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     ...
# 
# @router.put("/profile", response_model=ApiResponse[UserResponse])
# async def update_profile(
#     user_in: UserUpdate,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     ...