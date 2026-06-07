from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class BillDelegationCreate(BaseModel):
    grantee_user_id: int = Field(..., description="被授权成员用户 ID")
    can_create: bool = Field(True, description="允许代录账单")
    can_update: bool = Field(True, description="允许修改账单")
    can_delete: bool = Field(False, description="允许删除账单")
    expires_at: Optional[datetime] = Field(None, description="授权过期时间（可选）")


class BillDelegationResponse(BaseModel):
    id: int
    family_id: int
    grantor_user_id: int
    grantee_user_id: int
    grantor_name: Optional[str] = None
    grantee_name: Optional[str] = None
    can_create: bool
    can_update: bool
    can_delete: bool
    is_active: bool
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BillDelegationListResponse(BaseModel):
    granted: List[BillDelegationResponse] = Field(default_factory=list, description="我授予他人的授权")
    received: List[BillDelegationResponse] = Field(default_factory=list, description="他人授予我的授权")
