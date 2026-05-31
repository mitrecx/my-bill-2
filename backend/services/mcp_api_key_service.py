import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from models.mcp_api_key import McpApiKey
from models.user import User

MCP_KEY_PREFIX = "mcp_"


def hash_mcp_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_mcp_api_key() -> str:
    return f"{MCP_KEY_PREFIX}{secrets.token_urlsafe(32)}"


def create_mcp_api_key(db: Session, user: User, name: str = "default") -> Tuple[McpApiKey, str]:
    """生成新的 MCP API Key，返回 (记录, 明文 key)。同一用户仅保留一个 active key。"""
    db.query(McpApiKey).filter(
        McpApiKey.user_id == user.id,
        McpApiKey.is_active == True,
    ).update({"is_active": False})

    raw_key = generate_mcp_api_key()
    record = McpApiKey(
        user_id=user.id,
        key_hash=hash_mcp_api_key(raw_key),
        key_prefix=raw_key[:12],
        name=name,
        is_active=True,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record, raw_key


def get_active_mcp_api_key(db: Session, user_id: int) -> Optional[McpApiKey]:
    return (
        db.query(McpApiKey)
        .filter(McpApiKey.user_id == user_id, McpApiKey.is_active == True)
        .order_by(McpApiKey.created_at.desc())
        .first()
    )


def revoke_mcp_api_key(db: Session, user_id: int) -> bool:
    updated = (
        db.query(McpApiKey)
        .filter(McpApiKey.user_id == user_id, McpApiKey.is_active == True)
        .update({"is_active": False})
    )
    db.commit()
    return updated > 0


def authenticate_mcp_api_key(db: Session, raw_key: str) -> Optional[User]:
    if not raw_key or not raw_key.startswith(MCP_KEY_PREFIX):
        return None

    key_hash = hash_mcp_api_key(raw_key)
    record = (
        db.query(McpApiKey)
        .filter(McpApiKey.key_hash == key_hash, McpApiKey.is_active == True)
        .first()
    )
    if not record:
        return None

    user = db.query(User).filter(User.id == record.user_id, User.is_active == True).first()
    if not user:
        return None

    record.last_used_at = datetime.now(timezone.utc)
    db.commit()
    return user
