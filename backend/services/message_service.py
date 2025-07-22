from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import Optional, List, Dict, Any
from models.message import Message, MessageAction
from models.user import User
from schemas.message import MessageCreate, MessageActionCreate, FamilyInviteData
from datetime import datetime


class MessageService:
    def __init__(self, db: Session):
        self.db = db

    def create_message(self, message_data: MessageCreate) -> Message:
        """创建消息"""
        db_message = Message(**message_data.model_dump())
        self.db.add(db_message)
        self.db.commit()
        self.db.refresh(db_message)
        return db_message

    def get_user_messages(
        self, 
        user_id: int, 
        page: int = 1, 
        size: int = 20,
        is_read: Optional[bool] = None
    ) -> tuple[List[Message], int]:
        """获取用户消息列表"""
        query = self.db.query(Message).filter(Message.receiver_id == user_id)
        
        if is_read is not None:
            query = query.filter(Message.is_read == is_read)
        
        total = query.count()
        messages = query.order_by(desc(Message.created_at)).offset((page - 1) * size).limit(size).all()
        
        return messages, total

    def mark_as_read(self, message_id: int, user_id: int) -> bool:
        """标记消息为已读"""
        message = self.db.query(Message).filter(
            and_(Message.id == message_id, Message.receiver_id == user_id)
        ).first()
        
        if message:
            message.is_read = True
            message.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False

    def create_message_action(self, action_data: MessageActionCreate, user_id: int) -> MessageAction:
        """创建消息操作"""
        db_action = MessageAction(
            message_id=action_data.message_id,
            user_id=user_id,
            action_type=action_data.action_type
        )
        self.db.add(db_action)
        self.db.commit()
        self.db.refresh(db_action)
        return db_action

    def create_family_invite_message(
        self, 
        inviter_id: int, 
        invitee_id: int, 
        family_id: int, 
        family_name: str
    ) -> Message:
        """创建家庭邀请消息"""
        inviter = self.db.query(User).filter(User.id == inviter_id).first()
        inviter_name = inviter.full_name or inviter.username if inviter else "未知用户"
        
        invite_data = FamilyInviteData(
            family_id=family_id,
            family_name=family_name,
            inviter_name=inviter_name
        )
        
        message_data = MessageCreate(
            sender_id=inviter_id,
            receiver_id=invitee_id,
            message_type="FAMILY_INVITE",
            title="家庭邀请",
            content=f"{inviter_name} 邀请你加入 {family_name} 家庭",
            data=invite_data.model_dump()
        )
        
        return self.create_message(message_data)

    def create_system_message(
        self, 
        receiver_id: int, 
        title: str, 
        content: str, 
        data: Optional[Dict[str, Any]] = None
    ) -> Message:
        """创建系统消息"""
        message_data = MessageCreate(
            sender_id=None,  # 系统消息
            receiver_id=receiver_id,
            message_type="SYSTEM",
            title=title,
            content=content,
            data=data
        )
        
        return self.create_message(message_data)

    def get_unread_count(self, user_id: int) -> int:
        """获取未读消息数量"""
        return self.db.query(Message).filter(
            and_(Message.receiver_id == user_id, Message.is_read == False)
        ).count()

    def delete_message(self, message_id: int, user_id: int) -> bool:
        """删除消息（只能删除自己接收的消息）"""
        message = self.db.query(Message).filter(
            and_(Message.id == message_id, Message.receiver_id == user_id)
        ).first()
        
        if message:
            self.db.delete(message)
            self.db.commit()
            return True
        return False