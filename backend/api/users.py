from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime

from config.database import get_db
from models.user import User
from models.family import FamilyMember
from api.auth import get_current_user, get_password_hash
from schemas.common import ApiResponse
from pydantic import BaseModel, validator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('用户名至少需要3个字符')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码至少需要6个字符')
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if v is not None and len(v) < 6:
            raise ValueError('密码至少需要6个字符')
        return v


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    email: Optional[str]
    created_at: datetime
    family_name: Optional[str] = None
    family_role: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    page_size: int


@router.get("/", response_model=ApiResponse[UserListResponse])
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户列表（分页）"""
    try:
        # 构建查询
        query = db.query(User)
        
        if search:
            query = query.filter(
                User.username.contains(search) | 
                User.full_name.contains(search)
            )
        
        # 计算总数
        total = query.count()
        
        # 分页查询
        offset = (page - 1) * page_size
        users = query.offset(offset).limit(page_size).all()
        
        # 获取用户的家庭信息
        user_responses = []
        for user in users:
            family_member = db.query(FamilyMember).filter(
                FamilyMember.user_id == user.id
            ).first()
            
            user_response = UserResponse(
                id=user.id,
                username=user.username,
                full_name=user.full_name,
                email=user.email,
                created_at=user.created_at,
                family_name=family_member.family.family_name if family_member else None,
                family_role=family_member.role if family_member else None
            )
            user_responses.append(user_response)
        
        return ApiResponse(
            data=UserListResponse(
                users=user_responses,
                total=total,
                page=page,
                page_size=page_size
            )
        )
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取用户列表失败")


@router.post("/", response_model=ApiResponse[UserResponse])
async def create_user(
    user_in: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新用户"""
    try:
        # 检查用户名是否已存在
        existing_user = db.query(User).filter(User.username == user_in.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="用户名已存在")
        
        # 创建用户
        hashed_password = get_password_hash(user_in.password)
        user = User(
            username=user_in.username,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            email=user_in.email
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            created_at=user.created_at
        )
        
        return ApiResponse(data=user_response)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建用户失败: {e}")
        raise HTTPException(status_code=500, detail="创建用户失败")


@router.get("/{user_id}", response_model=ApiResponse[UserResponse])
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户详情"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 获取家庭信息
        family_member = db.query(FamilyMember).filter(
            FamilyMember.user_id == user.id
        ).first()
        
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            created_at=user.created_at,
            family_name=family_member.family.family_name if family_member else None,
            family_role=family_member.role if family_member else None
        )
        
        return ApiResponse(data=user_response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取用户详情失败")


@router.put("/{user_id}", response_model=ApiResponse[UserResponse])
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户信息"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 更新字段
        if user_in.full_name is not None:
            user.full_name = user_in.full_name
        if user_in.email is not None:
            user.email = user_in.email
        if user_in.password is not None:
            user.hashed_password = get_password_hash(user_in.password)
        
        db.commit()
        db.refresh(user)
        
        # 获取家庭信息
        family_member = db.query(FamilyMember).filter(
            FamilyMember.user_id == user.id
        ).first()
        
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            created_at=user.created_at,
            family_name=family_member.family.family_name if family_member else None,
            family_role=family_member.role if family_member else None
        )
        
        return ApiResponse(data=user_response)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新用户失败: {e}")
        raise HTTPException(status_code=500, detail="更新用户失败")


@router.delete("/{user_id}", response_model=ApiResponse[str])
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除用户"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 检查是否为当前用户
        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="不能删除自己")
        
        # 检查用户是否为家庭管理员
        family_member = db.query(FamilyMember).filter(
            FamilyMember.user_id == user.id,
            FamilyMember.role == "admin"
        ).first()
        
        if family_member:
            # 检查家庭是否还有其他成员
            other_members = db.query(FamilyMember).filter(
                FamilyMember.family_id == family_member.family_id,
                FamilyMember.user_id != user.id
            ).count()
            
            if other_members > 0:
                raise HTTPException(
                    status_code=400, 
                    detail="该用户是家庭管理员且家庭中还有其他成员，请先转让管理权限"
                )
        
        # 删除用户（级联删除相关数据）
        db.delete(user)
        db.commit()
        
        return ApiResponse(data="用户删除成功")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除用户失败: {e}")
        raise HTTPException(status_code=500, detail="删除用户失败")