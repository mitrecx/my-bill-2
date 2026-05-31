from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from config.database import Base


class McpApiKey(Base):
    """用户 MCP API Key，用于外部 MCP 客户端认证"""

    __tablename__ = "mcp_api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    key_prefix = Column(String(12), nullable=False, comment="Key 前缀，用于展示")
    name = Column(String(100), nullable=True, default="default")
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", backref="mcp_api_keys")

    def __repr__(self):
        return f"<McpApiKey(id={self.id}, user_id={self.user_id}, prefix={self.key_prefix})>"
