from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal


class BillBase(BaseModel):
    """账单基础模型"""
    amount: float = Field(..., ge=0, description="金额")
    transaction_type: str = Field(..., description="交易类型")
    merchant_name: Optional[str] = Field(None, max_length=200, description="商户名称")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    notes: Optional[str] = Field(None, max_length=1000, description="备注")
    payment_method: Optional[str] = Field(None, max_length=100, description="支付方式")
    category_id: Optional[int] = Field(None, description="分类ID")


class BillCreate(BillBase):
    """创建账单请求模型"""
    transaction_time: datetime = Field(..., description="交易时间")
    source_type: str = Field(..., description="来源类型")
    family_id: int = Field(..., description="家庭ID")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="原始数据")


class BillUpdate(BaseModel):
    """更新账单请求模型"""
    amount: Optional[float] = Field(None, ge=0, description="金额")
    transaction_type: Optional[str] = Field(None, description="交易类型")
    merchant_name: Optional[str] = Field(None, max_length=200, description="商户名称")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    notes: Optional[str] = Field(None, max_length=1000, description="备注")
    payment_method: Optional[str] = Field(None, max_length=100, description="支付方式")
    category_id: Optional[int] = Field(None, description="分类ID")


class CategoryResponse(BaseModel):
    """分类响应模型"""
    id: int
    name: str
    description: Optional[str]
    icon: Optional[str]
    color: Optional[str]

    class Config:
        from_attributes = True


class FamilySimpleResponse(BaseModel):
    """简化的家庭响应模型"""
    id: int
    name: str

    class Config:
        from_attributes = True


class UserSimpleResponse(BaseModel):
    """简化的用户响应模型"""
    id: int
    username: str
    full_name: Optional[str]

    class Config:
        from_attributes = True


class BillResponse(BaseModel):
    """账单响应模型"""
    id: int
    amount: float
    transaction_time: datetime
    transaction_type: str
    merchant_name: Optional[str]
    description: Optional[str]
    notes: Optional[str]
    payment_method: Optional[str]
    source_type: str
    category: Optional[CategoryResponse]
    family: FamilySimpleResponse
    user: UserSimpleResponse
    raw_data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class BillListResponse(BaseModel):
    """账单列表响应模型"""
    bills: List[BillResponse]
    total: int
    page: int
    size: int
    pages: int


class BillStatsResponse(BaseModel):
    """账单统计响应模型"""
    total_income: float
    total_expense: float
    total_count: int
    income_count: int
    expense_count: int
    avg_amount: float
    by_category: Dict[str, Dict[str, Any]]
    by_source: Dict[str, Dict[str, Any]]
    by_month: Dict[str, Dict[str, Any]]


class BillFilter(BaseModel):
    """账单筛选模型"""
    family_id: Optional[int] = None
    category_id: Optional[int] = None
    transaction_type: Optional[str] = None
    source_type: Optional[str] = None
    merchant_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    search: Optional[str] = None


class BillCategoryCreate(BaseModel):
    """创建账单分类请求模型"""
    name: str = Field(..., max_length=100, description="分类名称")
    description: Optional[str] = Field(None, max_length=500, description="分类描述")
    icon: Optional[str] = Field(None, max_length=50, description="图标")
    color: Optional[str] = Field(None, max_length=20, description="颜色")
    family_id: int = Field(..., description="家庭ID")


class BillCategoryUpdate(BaseModel):
    """更新账单分类请求模型"""
    name: Optional[str] = Field(None, max_length=100, description="分类名称")
    description: Optional[str] = Field(None, max_length=500, description="分类描述")
    icon: Optional[str] = Field(None, max_length=50, description="图标")
    color: Optional[str] = Field(None, max_length=20, description="颜色")


class BillCategoryResponse(BaseModel):
    """账单分类响应模型"""
    id: int
    name: str
    description: Optional[str]
    icon: Optional[str]
    color: Optional[str]
    family_id: int
    bills_count: Optional[int] = 0
    created_at: datetime

    class Config:
        from_attributes = True 