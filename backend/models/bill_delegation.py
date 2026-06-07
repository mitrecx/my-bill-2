from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from config.database import Base


class BillDelegation(Base):
    __tablename__ = "bill_delegations"

    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("families.id"), nullable=False)
    grantor_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    grantee_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    can_create = Column(Boolean, nullable=False, default=True)
    can_update = Column(Boolean, nullable=False, default=True)
    can_delete = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    grantor = relationship("User", foreign_keys=[grantor_user_id])
    grantee = relationship("User", foreign_keys=[grantee_user_id])
    family = relationship("Family")
