from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, validator


class ClassificationRuleBase(BaseModel):
    rule_text: str = Field(
        ...,
        description="供 AI 参考的自然语言规则描述（如商户名、关键词短语），非正则表达式",
    )
    source_type: Literal["alipay", "jd", "cmb", "wechat", "meituan", "manual", "all"] = Field(..., description="账单来源类型")
    target_category: str = Field(..., description="目标分类名称")
    transaction_type: Literal["expense", "income", "transfer"] = Field(
        default="expense",
        description="适用交易类型：expense=支出，income=收入，transfer=不计收支",
    )
    priority: int = Field(default=0, description="规则优先级，数字越大优先级越高")
    is_active: bool = Field(default=True, description="规则是否启用")


class ClassificationRuleCreate(ClassificationRuleBase):
    """创建分类规则的请求模型"""
    
    @validator('rule_text')
    def rule_text_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('规则描述不能为空')
        return v.strip()
    
    @validator('target_category')
    def target_category_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('目标分类不能为空')
        return v.strip()


class ClassificationRuleUpdate(BaseModel):
    """更新分类规则的请求模型"""
    rule_text: Optional[str] = None
    source_type: Optional[Literal["alipay", "jd", "cmb", "wechat", "meituan", "manual", "all"]] = None
    target_category: Optional[str] = None
    transaction_type: Optional[Literal["expense", "income", "transfer"]] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    
    @validator('rule_text')
    def rule_text_must_not_be_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('规则描述不能为空')
        return v.strip() if v else v
    
    @validator('target_category')
    def target_category_must_not_be_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('目标分类不能为空')
        return v.strip() if v else v


class ClassificationRuleResponse(ClassificationRuleBase):
    """分类规则的响应模型"""
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ClassificationRuleListResponse(BaseModel):
    """分类规则列表的响应模型"""
    rules: list[ClassificationRuleResponse]
    total: int
    page: int
    page_size: int


class ClassificationRuleBatchCreate(BaseModel):
    """批量创建分类规则的请求模型"""
    rules: list[ClassificationRuleCreate] = Field(..., description="规则列表")
    
    @validator('rules')
    def rules_must_not_be_empty(cls, v):
        if not v:
            raise ValueError('规则列表不能为空')
        return v


class ClassificationRuleTestRequest(BaseModel):
    """测试分类规则的请求模型"""
    rule_text: str = Field(..., description="要测试的规则")
    source_type: Literal["alipay", "jd", "cmb", "wechat", "meituan", "manual", "all"] = Field(..., description="账单来源类型")
    test_bills: list[dict] = Field(..., description="用于测试的账单数据")


class ClassificationRuleTestResponse(BaseModel):
    """测试分类规则的响应模型"""
    rule_text: str
    source_type: str
    matched_bills: list[dict] = Field(..., description="匹配的账单")
    total_matched: int = Field(..., description="匹配的账单数量")
    suggestions: list[str] = Field(default=[], description="优化建议")