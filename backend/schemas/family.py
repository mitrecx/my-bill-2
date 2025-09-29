from pydantic import BaseModel
from typing import Optional, List, Generic, TypeVar
from datetime import datetime
from .user import UserResponse

T = TypeVar("T")

class FamilyBase(BaseModel):
    family_name: str
    description: Optional[str] = None

class FamilyCreate(FamilyBase):
    # 新增：可选的邀请用户名列表，用于创建家庭时发送邀请
    invite_usernames: Optional[List[str]] = None

class FamilyUpdate(BaseModel):
    family_name: Optional[str] = None
    description: Optional[str] = None

class FamilyResponse(FamilyBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FamilyMemberBase(BaseModel):
    role: str

class FamilyMemberCreate(FamilyMemberBase):
    user_id: int

class FamilyMemberResponse(BaseModel):
    id: int
    user_id: int
    role: str
    joined_at: datetime
    # 嵌套返回用户信息，前端表格按 user.username / user.full_name 显示
    user: Optional[UserResponse] = None  # 直接引用，避免前向引用报错

    class Config:
        from_attributes = True

class FamilyWithMembersResponse(FamilyResponse):
    members: List[FamilyMemberResponse]