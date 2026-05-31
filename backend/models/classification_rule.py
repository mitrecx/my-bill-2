from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from config.database import Base


class ClassificationRule(Base):
    """分类规则：personal 仅对创建者生效，family 对家庭成员共享；AI 自动分类时注入提示词供优先参考。"""
    __tablename__ = "classification_rules"

    id = Column(Integer, primary_key=True, index=True)
    scope = Column(String(20), nullable=False, default="personal")
    family_id = Column(Integer, ForeignKey("families.id"), nullable=True, index=True)
    rule_text = Column(String, nullable=False)
    source_type = Column(String(20), nullable=False)
    target_category = Column(String(50), nullable=False)
    transaction_type = Column(String(20), nullable=False, default="expense")
    priority = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "source_type IN ('alipay', 'jd', 'cmb', 'wechat', 'meituan', 'manual', 'all')",
            name='check_source_type',
        ),
        CheckConstraint(
            "transaction_type IN ('expense', 'income', 'transfer')",
            name='check_classification_rule_transaction_type',
        ),
        CheckConstraint(
            "scope IN ('personal', 'family')",
            name='check_classification_rule_scope',
        ),
        CheckConstraint(
            "(scope = 'personal' AND family_id IS NULL) OR (scope = 'family' AND family_id IS NOT NULL)",
            name='check_classification_rule_scope_family_id',
        ),
    )

    family = relationship("Family", foreign_keys=[family_id])
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return (
            f"<ClassificationRule(id={self.id}, scope='{self.scope}', "
            f"target_category='{self.target_category}')>"
        )
