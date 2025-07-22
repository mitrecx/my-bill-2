from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from config.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    #
    # Back-populates,双向关系，用于高效查询
    #

    # 用户创建的家庭
    owned_families = relationship("Family", back_populates="owner")
    
    # 用户所属的家庭成员关系
    family_members = relationship("FamilyMember", back_populates="user")
    
    # 账单
    bills = relationship("Bill", back_populates="user")
    
    # 上传记录
    uploads = relationship("UploadRecord", back_populates="user") 