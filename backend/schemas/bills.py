from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, TypeVar, Generic
from datetime import datetime, date
from decimal import Decimal

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """通用API响应模型"""
    data: T
    success: bool = True
    message: Optional[str] = None


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
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None

    class Config:
        from_attributes = True
        
    @classmethod
    def from_category(cls, category):
        """从BillCategory模型创建响应"""
        if not category:
            return None
        return cls(
            id=category.id,
            name=category.category_name,
            description=getattr(category, 'description', None),
            icon=category.icon,
            color=category.color
        )


class FamilySimpleResponse(BaseModel):
    """简化的家庭响应模型"""
    id: int
    name: str

    class Config:
        from_attributes = True
        
    @classmethod
    def from_family(cls, family):
        """从Family模型创建响应"""
        return cls(
            id=family.id,
            name=family.family_name
        )


class UserSimpleResponse(BaseModel):
    """简化的用户响应模型"""
    id: int
    username: str
    full_name: Optional[str] = None

    class Config:
        from_attributes = True
        
    @classmethod
    def from_user(cls, user):
        """从User模型创建响应"""
        if not user:
            return None
        return cls(
            id=user.id,
            username=user.username,
            full_name=user.full_name
        )


class BillResponse(BaseModel):
    """账单响应模型"""
    id: int
    amount: float
    transaction_date: datetime  # 改为transaction_date以匹配前端期望
    transaction_type: str
    transaction_desc: Optional[str] = None  # 对应数据库中的transaction_desc字段
    source_type: str
    category: Optional[CategoryResponse] = None
    family: Optional[FamilySimpleResponse] = None
    user: Optional[UserSimpleResponse] = None
    raw_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        
    @classmethod
    def from_bill(cls, bill):
        """从Bill模型创建响应"""
        # 映射中文交易类型到英文
        transaction_type_map = {
            "收入": "income",
            "支出": "expense"
        }
        transaction_type = transaction_type_map.get(bill.transaction_type, bill.transaction_type)
        
        return cls(
            id=bill.id,
            amount=bill.amount,
            transaction_date=bill.transaction_time,  # 映射字段名
            transaction_type=transaction_type,  # 使用映射后的值
            transaction_desc=bill.transaction_desc,
            source_type=bill.source_type,
            category=CategoryResponse.from_category(bill.category) if bill.category else None,
            family=FamilySimpleResponse.from_family(bill.family) if bill.family else None,
            user=UserSimpleResponse.from_user(bill.user) if bill.user else None,
            raw_data=bill.raw_data,
            created_at=bill.created_at,
            updated_at=bill.updated_at
        )


class BillListResponse(BaseModel):
    """账单列表响应模型"""
    items: List[BillResponse]  # 改为items以符合前端期望
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
        
    @classmethod
    def from_orm(cls, category):
        """从BillCategory模型创建响应"""
        if not category:
            return None
        return cls(
            id=category.id,
            name=category.category_name,  # 映射category_name到name
            description=getattr(category, 'description', None),
            icon=category.icon,
            color=category.color,
            family_id=category.family_id,
            bills_count=getattr(category, 'bills_count', 0),
            created_at=category.created_at
        )