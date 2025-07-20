from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 系统消息时为空
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_type = Column(String(50), nullable=False)  # system, family_invite, etc.
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)  # 额外数据，如邀请信息
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")
    actions = relationship("MessageAction", back_populates="message", cascade="all, delete-orphan")


class MessageAction(Base):
    __tablename__ = "message_actions"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action_type = Column(String(50), nullable=False)  # accept, reject, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    message = relationship("Message", back_populates="actions")
    user = relationship("User", back_populates="message_actions")