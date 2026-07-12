from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from config.database import get_db
from api.auth import get_current_user
from models.message import Message
from models.user import User
from services.message_service import MessageService
from schemas.message import (
    MessageResponse,
    MessageListResponse,
    MessageActionCreate,
    MessageActionResponse,
    MessageUpdate,
)
from schemas.common import ApiResponse

router = APIRouter(prefix="/messages", tags=["messages"])


def _list_messages(
    message_service: MessageService,
    user_id: int,
    *,
    page: int,
    size: int,
    is_read: Optional[bool],
) -> ApiResponse[MessageListResponse]:
    messages, total = message_service.get_user_messages(
        user_id=user_id,
        page=page,
        size=size,
        is_read=is_read,
    )
    pages = math.ceil(total / size) if total else 0
    return ApiResponse(
        data=MessageListResponse(
            items=[MessageResponse.model_validate(msg) for msg in messages],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )
    )


@router.get("", response_model=ApiResponse[MessageListResponse])
async def get_my_messages(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    is_read: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的消息列表。"""
    effective_size = page_size or size
    message_service = MessageService(db)
    return _list_messages(
        message_service,
        current_user.id,
        page=page,
        size=effective_size,
        is_read=is_read,
    )


@router.get("/user/{user_id}", response_model=ApiResponse[MessageListResponse])
async def get_messages_for_user(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    is_read: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取指定用户的消息列表（仅允许查询本人）。"""
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看他人的消息")
    message_service = MessageService(db)
    return _list_messages(
        message_service,
        user_id,
        page=page,
        size=size,
        is_read=is_read,
    )


@router.get("/unread-count", response_model=ApiResponse[int])
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取未读消息数量。"""
    message_service = MessageService(db)
    count = message_service.get_unread_count(current_user.id)
    return ApiResponse(data=count)


@router.patch("/{message_id}", response_model=ApiResponse[MessageResponse])
async def update_message(
    message_id: int,
    message_update: MessageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新消息（如标记为已读）。"""
    message_service = MessageService(db)

    if message_update.is_read is not None:
        success = message_service.mark_as_read(message_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="消息不存在")

    message = (
        db.query(Message)
        .filter(Message.id == message_id, Message.receiver_id == current_user.id)
        .first()
    )
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")

    return ApiResponse(data=MessageResponse.model_validate(message))


@router.post("/{message_id}/actions", response_model=ApiResponse[MessageActionResponse])
async def create_message_action(
    message_id: int,
    action_data: MessageActionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建消息操作（如接受/拒绝邀请）。"""
    message_service = MessageService(db)

    message = (
        db.query(Message)
        .filter(Message.id == message_id, Message.receiver_id == current_user.id)
        .first()
    )
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")

    action_data.message_id = message_id
    action = message_service.create_message_action(action_data, current_user.id)

    if message.message_type == "FAMILY_INVITE" and action_data.action_type in ["accept", "reject"]:
        await _handle_family_invite_action(message, action_data.action_type, current_user, db)

    return ApiResponse(data=MessageActionResponse.model_validate(action))


@router.delete("/{message_id}", response_model=ApiResponse[bool])
async def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除消息。"""
    message_service = MessageService(db)
    success = message_service.delete_message(message_id, current_user.id)

    if not success:
        raise HTTPException(status_code=404, detail="消息不存在")

    return ApiResponse(data=True)


async def _handle_family_invite_action(message, action_type: str, user: User, db: Session):
    """处理家庭邀请操作。"""
    if not message.data or "family_id" not in message.data:
        return

    family_id = message.data["family_id"]

    if action_type == "accept":
        from services.family_service import FamilyService

        family_service = FamilyService(db)

        try:
            family_service.add_member_to_family(family_id, user.id)

            message_service = MessageService(db)
            message_service.create_system_message(
                receiver_id=user.id,
                title="加入家庭成功",
                content=f"你已成功加入 {message.data.get('family_name', '家庭')}",
            )
        except Exception as e:
            message_service = MessageService(db)
            message_service.create_system_message(
                receiver_id=user.id,
                title="加入家庭失败",
                content=f"加入家庭失败：{str(e)}",
            )
    elif action_type == "reject":
        message_service = MessageService(db)
        message_service.create_system_message(
            receiver_id=user.id,
            title="已拒绝邀请",
            content=f"你已拒绝加入 {message.data.get('family_name', '家庭')} 的邀请",
        )
