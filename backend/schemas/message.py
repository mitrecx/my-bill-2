from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime


class MessageBase(BaseModel):
    title: str
    content: str
    message_type: str
    data: Optional[Dict[str, Any]] = None


class MessageCreate(MessageBase):
    receiver_id: int
    sender_id: Optional[int] = None


class MessageUpdate(BaseModel):
    is_read: Optional[bool] = None


class MessageResponse(MessageBase):
    id: int
    sender_id: Optional[int]
    receiver_id: int
    is_read: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageActionBase(BaseModel):
    action_type: str


class MessageActionCreate(MessageActionBase):
    message_id: int


class MessageActionResponse(MessageActionBase):
    id: int
    message_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    total: int
    page: int
    size: int
    pages: int


class FamilyInviteData(BaseModel):
    family_id: int
    family_name: str
    inviter_name: str