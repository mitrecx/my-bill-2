from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from config.database import Base


class BillCategory(Base):
    __tablename__ = "bill_categories"

    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String, nullable=False)
    parent_id = Column(Integer, nullable=True)
    color = Column(String, nullable=True)
    icon = Column(String, nullable=True)
    category_type = Column(String, nullable=False, default="expense")  # income 或 expense
    description = Column(String, nullable=True)  # 新增：分类描述
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    bills = relationship("Bill", back_populates="category")


class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("bill_categories.id"), nullable=True)

    transaction_time = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String, nullable=False)  # income, expense
    transaction_desc = Column(String, nullable=True)
    source_type = Column(String, nullable=False)  # alipay, jd, cmb
    source_filename = Column(String, nullable=True)  # 新增：记录来源文件名
    currency = Column(String, nullable=True)  # 新增：货币字段
    remark = Column(String, nullable=True)  # 新增：备注字段
    raw_data = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="bills")
    category = relationship("BillCategory", back_populates="bills")