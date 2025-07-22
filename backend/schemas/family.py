from pydantic import BaseModel
from typing import Optional, List, Generic, TypeVar
from datetime import datetime

T = TypeVar("T")

class FamilyBase(BaseModel):
    family_name: str
    description: Optional[str] = None

class FamilyCreate(FamilyBase):
    pass

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
    username: str  # 从 user 对象中获取

    class Config:
        from_attributes = True

class FamilyWithMembersResponse(FamilyResponse):
    members: List[FamilyMemberResponse] 