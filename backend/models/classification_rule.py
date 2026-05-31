from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from config.database import Base


class ClassificationRule(Base):
    """用户自定义分类规则，在 AI 自动分类时注入提示词供优先参考（非程序硬匹配）。"""
    __tablename__ = "classification_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_text = Column(String, nullable=False)
    source_type = Column(String(20), nullable=False)
    target_category = Column(String(50), nullable=False)
    transaction_type = Column(String(20), nullable=False, default="expense")
    priority = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # 不能为空
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 添加约束
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('alipay', 'jd', 'cmb', 'wechat', 'meituan', 'manual', 'all')",
            name='check_source_type'
        ),
        CheckConstraint(
            "transaction_type IN ('expense', 'income', 'transfer')",
            name='check_classification_rule_transaction_type'
        ),
        # 用户隔离的唯一约束
        UniqueConstraint(
            'created_by', 'rule_text', 'source_type', 'transaction_type',
            name='uq_classification_rules_user_rule_source_type',
        ),
    )

    # 关系
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<ClassificationRule(id={self.id}, source_type='{self.source_type}', target_category='{self.target_category}')>"