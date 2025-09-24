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
    description: Optional[str] = Field(None, max_length=500, description="描述")
    notes: Optional[str] = Field(None, max_length=1000, description="备注")

    category_id: Optional[int] = Field(None, description="分类ID")


class BillCreate(BillBase):
    """创建账单请求模型"""
    transaction_time: datetime = Field(..., description="交易时间")
    source_type: str = Field(..., description="来源类型")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="原始数据")


class BillUpdate(BaseModel):
    """更新账单请求模型"""
    amount: Optional[float] = Field(None, ge=0, description="金额")
    transaction_type: Optional[str] = Field(None, description="交易类型")
    transaction_desc: Optional[str] = Field(None, max_length=500, description="交易描述")
    category_id: Optional[int] = Field(None, description="分类ID")
    remark: Optional[str] = Field(None, max_length=1000, description="备注")


class CategoryResponse(BaseModel):
    """分类响应模型"""
    id: int
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    category_type: str = Field(..., description="分类类型：income 或 expense")

    class Config:
        from_attributes = True
        
    @classmethod
    def from_category(cls, category):
        """从BillCategory模型创建响应"""
        if not category:
            return None
        
        # 确保所有必需字段都有值
        name = getattr(category, 'category_name', None) or '未分类'
        category_type = getattr(category, 'category_type', None) or 'expense'
        
        return cls(
            id=category.id,
            name=name,
            description=getattr(category, 'description', None),
            icon=getattr(category, 'icon', None),
            color=getattr(category, 'color', None),
            category_type=category_type
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
            "支出": "expense",
            "不计收支": "transfer"  # 添加不计收支类型
        }
        transaction_type = transaction_type_map.get(bill.transaction_type, bill.transaction_type)
        
        # 确保必需字段都有值
        transaction_date = bill.transaction_time or bill.created_at
        created_at = bill.created_at or datetime.utcnow()
        
        return cls(
            id=bill.id,
            amount=bill.amount,
            transaction_date=transaction_date,  # 确保有值
            transaction_type=transaction_type,  # 使用映射后的值
            transaction_desc=bill.transaction_desc,
            source_type=bill.source_type,
            category=CategoryResponse.from_category(bill.category) if bill.category else None,
            family=None,  # 暂时设为None，后续可以通过用户的家庭关系获取
            user=UserSimpleResponse.from_user(bill.user) if bill.user else None,
            raw_data=bill.raw_data,
            created_at=created_at,
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


# 新增：分类统计项
class CategoryStatsItem(BaseModel):
    category_id: int
    category_name: str
    total_amount: float
    transaction_count: int
    percentage: float


class BillFilter(BaseModel):
    """账单筛选模型"""
    category_id: Optional[int] = None
    transaction_type: Optional[str] = None
    source_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    search: Optional[str] = None


class BillCategoryCreate(BaseModel):
    """创建账单分类请求模型"""
    name: str = Field(..., max_length=100, description="分类名称")
    category_type: Optional[str] = Field("expense", description="分类类型：income 或 expense，默认 expense")
    description: Optional[str] = Field(None, max_length=500, description="分类描述")
    icon: Optional[str] = Field(None, max_length=50, description="图标")
    color: Optional[str] = Field(None, max_length=20, description="颜色")


class BillCategoryUpdate(BaseModel):
    """更新账单分类请求模型"""
    name: Optional[str] = Field(None, max_length=100, description="分类名称")
    category_type: Optional[str] = Field(None, description="分类类型：income 或 expense")
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
    category_type: str  # income 或 expense
    bills_count: Optional[int] = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

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
            category_type=category.category_type,  # 添加分类类型
            bills_count=getattr(category, 'bills_count', 0),
            created_at=category.created_at,
            updated_at=getattr(category, 'updated_at', getattr(category, 'created_at', None))
        )


class FinanceSummaryResponse(BaseModel):
    """财务汇总响应模型：按年或按月聚合的金额与笔数"""
    year: int = Field(..., description="年份")
    month: Optional[int] = Field(None, ge=1, le=12, description="月份（可选，按月查询时返回）")
    result_type: str = Field(..., description="结果类型：income/expense/surplus")
    amount: float = Field(..., description="金额（精确到小数点后两位）")
    count: int = Field(..., description="交易笔数")


class MonthlyExpenseItem(BaseModel):
    month: int
    month_name: str
    amount: float
    income: float = 0.0


class YearlyExpenseChartResponse(BaseModel):
    monthly_expenses: List[MonthlyExpenseItem]
    total_year_expense: float
    total_year_income: float


# 新增：日度支出项与月度支出趋势响应模型
class DailyExpenseItem(BaseModel):
    day: int = Field(..., ge=1, le=31, description="日")
    date_str: str = Field(..., description="日期字符串 YYYY-MM-DD")
    amount: float = Field(..., ge=0, description="当天支出金额")


class MonthlyExpenseTrendResponse(BaseModel):
    year: int = Field(..., description="年份")
    month: int = Field(..., ge=1, le=12, description="月份")
    days: List[DailyExpenseItem]
    total_month_expense: float = Field(..., description="本月总支出")


class FinanceSummaryResponse(BaseModel):
    total_income: float
    total_expense: float
    total_count: int
    income_count: int
    expense_count: int
    avg_amount: float
    by_category: Dict[str, Dict[str, Any]]
    by_source: Dict[str, Dict[str, Any]]
    by_month: Dict[str, Dict[str, Any]]