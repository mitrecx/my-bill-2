from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

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

class FamilyMemberResponse(FamilyMemberBase):
    id: int
    family_id: int
    user_id: int
    joined_at: datetime

    class Config:
        from_attributes = True

class FamilyWithMembersResponse(FamilyResponse):
    members: List[FamilyMemberResponse] 