from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, cast, Numeric, case
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import logging

from config.database import get_db
from models.user import User
from models.bill import Bill, BillCategory
from models.family import FamilyMember
from api.auth import get_current_user
from schemas.bills import (
    BillResponse,
    BillListResponse,
    BillStatsResponse,
    BillFilter,
    BillCreate,
    BillUpdate,
    BillCategoryCreate,
    BillCategoryUpdate,
    BillCategoryResponse,
    ApiResponse,
    FinanceSummaryResponse,
    CategoryStatsItem,
    YearlyExpenseChartResponse,
    MonthlyExpenseItem,
)
from services.ai_classification_service import ai_classification_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bills", tags=["bills"])


async def get_user_family_members(user: User, db: Session) -> List[int]:
    """获取用户家庭中所有成员的用户ID列表（包括自己）"""
    # 获取用户所属的家庭
    family_member = db.query(FamilyMember).filter(
        FamilyMember.user_id == user.id
    ).first()
    
    if not family_member:
        # 如果用户不在任何家庭中，只返回自己的ID
        return [user.id]
    
    # 获取家庭中所有成员的用户ID
    family_members = db.query(FamilyMember).filter(
        FamilyMember.family_id == family_member.family_id
    ).all()
    
    return [fm.user_id for fm in family_members]


@router.get("", response_model=ApiResponse[BillListResponse])
async def get_bills(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    # 支持多选分类：同时兼容 category_id=1&category_id=2 以及 category_id[]=1&category_id[]=2 两种形式
    category_id: Optional[List[int]] = Query(None, description="分类ID筛选（可多选）"),
    category_id_brackets: Optional[List[int]] = Query(None, alias="category_id[]", description="分类ID筛选（可多选，方括号数组形式）"),
    transaction_type: Optional[str] = Query(None, description="交易类型筛选"),
    # 支持多选来源：同时兼容 source_type=a&source_type=b 以及 source_type[]=a&source_type[]=b 两种形式
    source_type: Optional[List[str]] = Query(None, description="来源类型筛选（可多选）"),
    source_type_brackets: Optional[List[str]] = Query(None, alias="source_type[]", description="来源类型筛选（可多选，方括号数组形式）"),

    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    min_amount: Optional[float] = Query(None, ge=0, description="最小金额"),
    max_amount: Optional[float] = Query(None, ge=0, description="最大金额"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: str = Query("transaction_time", description="排序字段"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序顺序"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取账单列表"""
    try:
        # 获取用户家庭中所有成员的用户ID
        family_user_ids = await get_user_family_members(current_user, db)
        
        # 构建查询
        query = db.query(Bill).options(
            joinedload(Bill.category),
            joinedload(Bill.user)
        ).filter(Bill.user_id.in_(family_user_ids))
        
        # 应用筛选条件
        # 合并两种形式的分类参数
        merged_category_ids: Optional[List[int]] = None
        if category_id:
            merged_category_ids = category_id
        if category_id_brackets:
            merged_category_ids = (merged_category_ids or []) + category_id_brackets
        if merged_category_ids:
            query = query.filter(Bill.category_id.in_(merged_category_ids))
        
        if transaction_type:
            # 将英文交易类型转换为中文进行数据库查询
            transaction_type_map = {
                "income": "收入",
                "expense": "支出",
                "transfer": "不计收支"  # 添加不计收支类型
            }
            db_transaction_type = transaction_type_map.get(transaction_type, transaction_type)
            query = query.filter(Bill.transaction_type == db_transaction_type)
        
        # 合并两种形式的来源参数，并支持多选
        merged_source_types: Optional[List[str]] = None
        if source_type:
            merged_source_types = source_type
        if source_type_brackets:
            merged_source_types = (merged_source_types or []) + source_type_brackets
        if merged_source_types:
            query = query.filter(Bill.source_type.in_(merged_source_types))
        
        if start_date:
            query = query.filter(Bill.transaction_time >= start_date)
        
        if end_date:
            # 结束日期包含当天，所以加1天（使用安全的timedelta避免月底溢出）
            query = query.filter(Bill.transaction_time < (end_date + timedelta(days=1)))
        
        if min_amount is not None:
            query = query.filter(Bill.amount >= min_amount)
        
        if max_amount is not None:
            query = query.filter(Bill.amount <= max_amount)
        
        if search:
            # 在描述中搜索关键词
            query = query.filter(
                Bill.transaction_desc.ilike(f"%{search}%")
            )
        
        # 排序
        if hasattr(Bill, sort_by):
            order_column = getattr(Bill, sort_by)
            if sort_order == "desc":
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(order_column)
        else:
            # 默认按交易时间倒序
            query = query.order_by(desc(Bill.transaction_time))
        
        # 分页
        total = query.count()
        pages = (total + size - 1) // size
        items = query.offset((page - 1) * size).limit(size).all()
        
        # 构建响应
        response_items = [BillResponse.from_bill(bill) for bill in items]
        response = BillListResponse(
            items=response_items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
        return ApiResponse[BillListResponse](
            data=response,
            success=True,
            message="获取账单列表成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取账单列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取账单列表失败"
        )


@router.get("/ai-classification/status", response_model=ApiResponse[Dict[str, Any]])
async def get_ai_classification_status(
    current_user: User = Depends(get_current_user)
):
    """获取AI分类服务状态"""
    try:
        status_info = {
            'available': ai_classification_service.is_available(),
            'service_name': 'GLM-4.5',
            'provider': '智谱AI'
        }
        
        if not ai_classification_service.is_available():
            status_info['error'] = '未配置ZHIPU_API_KEY或服务初始化失败'
        
        return ApiResponse(
            success=True,
            message="获取AI分类服务状态成功",
            data=status_info
        )
        
    except Exception as e:
        logger.error(f"获取AI分类服务状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取AI分类服务状态失败"
        )


@router.get("/finance-summary", response_model=ApiResponse[FinanceSummaryResponse], response_model_exclude_none=True)
async def get_finance_summary(
    result_type: str = Query(..., description="结果类型：income/expense/surplus"),
    year: int = Query(..., ge=1970, le=2100, description="年份"),
    month: Optional[int] = Query(None, ge=1, le=12, description="月份（可选）"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取财务汇总数据：按年或按月聚合。
    - 当传入月份时，返回指定年月的聚合结果
    - 当不传月份时，返回指定年份的聚合结果
    返回统一结构：年份、（按月查询时返回月份）、金额（两位小数）、交易笔数
    """
    try:
        # 校验 result_type
        allowed_types = {"income", "expense", "surplus"}
        if result_type not in allowed_types:
            raise HTTPException(status_code=400, detail="result_type 必须为 income/expense/surplus 之一")

        # 获取家庭相关用户ID
        family_user_ids = await get_user_family_members(current_user, db)

        # 计算时间范围
        if month:
            # 月度范围：[year-month-01, next month 01)
            if month == 12:
                start_dt = date(year, 12, 1)
                end_dt = date(year + 1, 1, 1)
            else:
                start_dt = date(year, month, 1)
                end_dt = date(year, month + 1, 1)
        else:
            # 年度范围：[year-01-01, next year 01-01)
            start_dt = date(year, 1, 1)
            end_dt = date(year + 1, 1, 1)

        # 公共过滤条件
        base_filters = [
            Bill.user_id.in_(family_user_ids),
            Bill.transaction_time >= start_dt,
            Bill.transaction_time < end_dt,
        ]

        # 定义中文交易类型映射
        db_type_map = {
            "income": "收入",
            "expense": "支出",
        }

        # 统计函数：金额使用numeric聚合，确保精度
        def sum_amount(filters):
            return db.query(
                func.coalesce(func.sum(cast(Bill.amount, Numeric(18, 4))), 0)
            ).filter(*filters).scalar()

        def count_bills(filters):
            return db.query(func.count(Bill.id)).filter(*filters).scalar()

        if result_type in ("income", "expense"):
            tx_type = db_type_map[result_type]
            filters = base_filters + [Bill.transaction_type == tx_type]
            total_amount_dec = sum_amount(filters)
            # 将Decimal/数值统一量化到两位小数
            total_amount = float(Decimal(total_amount_dec).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            total_count = int(count_bills(filters))
        else:
            # surplus = income - expense
            income_filters = base_filters + [Bill.transaction_type == db_type_map["income"]]
            expense_filters = base_filters + [Bill.transaction_type == db_type_map["expense"]]
            income_amount_dec = sum_amount(income_filters)
            expense_amount_dec = sum_amount(expense_filters)
            surplus_dec = Decimal(income_amount_dec) - Decimal(expense_amount_dec)
            total_amount = float(surplus_dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            total_count = int(count_bills(income_filters) + count_bills(expense_filters))

        response = FinanceSummaryResponse(
            year=year,
            month=month,
            result_type=result_type,
            amount=total_amount,
            count=total_count
        )

        return ApiResponse[FinanceSummaryResponse](
            data=response,
            success=True,
            message="获取财务汇总成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取财务汇总失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取财务汇总失败"
        )


@router.get("/finance-summary/batch", response_model=ApiResponse[List[FinanceSummaryResponse]], response_model_exclude_none=True)
async def get_finance_summary_batch(
    result_type: str = Query(..., description="结果类型：income/expense/surplus"),
    months: int = Query(12, ge=1, le=36, description="回溯月份数，默认12个月"),
    end_year: Optional[int] = Query(None, ge=1970, le=2100, description="结束年份（可选，默认为当前年）"),
    end_month: Optional[int] = Query(None, ge=1, le=12, description="结束月份（可选，默认为当前月）"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量获取最近N个月的财务汇总数据（默认12个月），单次查询高效聚合。
    - 若未传 end_year/end_month，则以当前年月为结束点（包含该月）
    - 返回从 (end - months + 1) 到 end 的每个月数据，按月份升序排列
    """
    try:
        allowed_types = {"income", "expense", "surplus"}
        if result_type not in allowed_types:
            raise HTTPException(status_code=400, detail="result_type 必须为 income/expense/surplus 之一")
        if months <= 0:
            raise HTTPException(status_code=400, detail="months 必须为正整数")

        # 结束年月：默认当前年月
        now = datetime.now()
        end_y = end_year or now.year
        end_m = end_month or now.month

        # 计算开始年月（包含）和结束边界（下个月的1号，不包含）
        # start: (end_y, end_m) 往前 (months - 1) 个月
        total_back = months - 1
        start_y = end_y
        start_m = end_m
        # 往前回滚 total_back 个月
        start_y -= (total_back // 12)
        start_m -= (total_back % 12)
        if start_m <= 0:
            # 借一年
            borrow = (abs(start_m) // 12) + 1
            start_y -= borrow
            start_m += 12 * borrow
        
        start_dt = date(start_y, start_m, 1)
        # end 边界为 end月的下月1号
        if end_m == 12:
            end_dt = date(end_y + 1, 1, 1)
        else:
            end_dt = date(end_y, end_m + 1, 1)

        # 获取家庭成员用户ID
        family_user_ids = await get_user_family_members(current_user, db)

        # 统一按月聚合，一次性查询收入/支出金额与笔数
        month_expr = func.date_trunc('month', Bill.transaction_time).label('month_start')
        income_amount_expr = func.coalesce(
            func.sum(case((Bill.transaction_type == "收入", cast(Bill.amount, Numeric(18, 4))), else_=0)), 0
        ).label("income_amount")
        expense_amount_expr = func.coalesce(
            func.sum(case((Bill.transaction_type == "支出", cast(Bill.amount, Numeric(18, 4))), else_=0)), 0
        ).label("expense_amount")
        income_count_expr = func.sum(case((Bill.transaction_type == "收入", 1), else_=0)).label("income_count")
        expense_count_expr = func.sum(case((Bill.transaction_type == "支出", 1), else_=0)).label("expense_count")

        rows = db.query(
            month_expr,
            income_amount_expr,
            expense_amount_expr,
            income_count_expr,
            expense_count_expr,
        ).filter(
            Bill.user_id.in_(family_user_ids),
            Bill.transaction_time >= start_dt,
            Bill.transaction_time < end_dt,
        ).group_by(month_expr).order_by(month_expr.asc()).all()

        # 将结果转为字典便于补齐月份
        monthly_map: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            month_start: datetime = r.month_start
            y = month_start.year
            m = month_start.month
            key = f"{y:04d}-{m:02d}"
            monthly_map[key] = {
                "income_amount": Decimal(str(r.income_amount)) if r.income_amount is not None else Decimal("0"),
                "expense_amount": Decimal(str(r.expense_amount)) if r.expense_amount is not None else Decimal("0"),
                "income_count": int(r.income_count or 0),
                "expense_count": int(r.expense_count or 0),
            }

        # 迭代每个月，补齐缺失月份
        def iter_months(y: int, m: int, count: int):
            cy, cm = y, m
            for _ in range(count):
                yield cy, cm
                # 前进一个月
                if cm == 12:
                    cy += 1
                    cm = 1
                else:
                    cm += 1
        
        results: List[FinanceSummaryResponse] = []
        for y, m in iter_months(start_y, start_m, months):
            key = f"{y:04d}-{m:02d}"
            data = monthly_map.get(key, {
                "income_amount": Decimal("0"),
                "expense_amount": Decimal("0"),
                "income_count": 0,
                "expense_count": 0,
            })

            if result_type == "income":
                amount_dec = data["income_amount"]
                cnt = data["income_count"]
            elif result_type == "expense":
                amount_dec = data["expense_amount"]
                cnt = data["expense_count"]
            else:
                amount_dec = data["income_amount"] - data["expense_amount"]
                cnt = data["income_count"] + data["expense_count"]

            amount = float(Decimal(amount_dec).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            count_val = int(cnt)

            results.append(FinanceSummaryResponse(
                year=y,
                month=m,
                result_type=result_type,
                amount=amount,
                count=count_val
            ))

        return ApiResponse[List[FinanceSummaryResponse]](
            data=results,
            success=True,
            message="获取批量财务汇总成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取批量财务汇总失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取批量财务汇总失败"
        )


@router.get("/stats", response_model=BillStatsResponse)
async def get_bill_stats(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取账单统计数据"""
    try:
        # 获取家庭成员用户ID集合
        family_user_ids = await get_user_family_members(current_user, db)

        # 基础查询
        q = db.query(Bill).filter(Bill.user_id.in_(family_user_ids))

        if start_date:
            q = q.filter(Bill.transaction_time >= start_date)

        if end_date:
            q = q.filter(Bill.transaction_time < (end_date + timedelta(days=1)))

        bills = q.all()

        # 计算统计数据
        total_income = sum(float(bill.amount) for bill in bills if bill.transaction_type == "收入")
        total_expense = sum(float(bill.amount) for bill in bills if bill.transaction_type == "支出")
        total_count = len(bills)
        income_count = len([bill for bill in bills if bill.transaction_type == "收入"])
        expense_count = len([bill for bill in bills if bill.transaction_type == "支出"])
        avg_amount = (total_income + total_expense) / total_count if total_count > 0 else 0.0

        # 按分类统计
        by_category = {}
        # 按来源统计
        by_source = {}
        # 按月份统计
        by_month = {}

        return BillStatsResponse(
            total_income=total_income,
            total_expense=total_expense,
            total_count=total_count,
            income_count=income_count,
            expense_count=expense_count,
            avg_amount=avg_amount,
            by_category=by_category,
            by_source=by_source,
            by_month=by_month
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取账单统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取账单统计失败"
        )


@router.get("/stats/categories", response_model=ApiResponse[List[CategoryStatsItem]])
async def get_category_stats(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取支出分类统计（用于分类饼图）"""
    try:
        # 获取家庭成员用户ID集合
        family_user_ids = await get_user_family_members(current_user, db)

        # 基础查询：仅统计支出
        q = db.query(
            BillCategory.id.label("category_id"),
            BillCategory.category_name.label("category_name"),
            func.coalesce(func.sum(Bill.amount), 0).label("total_amount"),
            func.count(Bill.id).label("transaction_count")
        ).join(Bill, Bill.category_id == BillCategory.id)
        
        q = q.filter(
            Bill.user_id.in_(family_user_ids),
            Bill.transaction_type == "支出"
        )

        if start_date:
            q = q.filter(Bill.transaction_time >= start_date)

        if end_date:
            q = q.filter(Bill.transaction_time < (end_date + timedelta(days=1)))

        q = q.group_by(BillCategory.id, BillCategory.category_name)
        q = q.order_by(desc("total_amount"))

        rows = q.all()

        total_amount = sum([float(r.total_amount) for r in rows]) if rows else 0.0
        items: List[CategoryStatsItem] = []
        for r in rows:
            amt = float(Decimal(str(r.total_amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            pct = (amt / total_amount * 100.0) if total_amount > 0 else 0.0
            items.append(CategoryStatsItem(
                category_id=r.category_id,
                category_name=r.category_name,
                total_amount=amt,
                transaction_count=int(r.transaction_count or 0),
                percentage=float(Decimal(str(pct)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            ))

        return ApiResponse[List[CategoryStatsItem]](
            data=items,
            success=True,
            message="获取分类统计成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分类统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取分类统计失败"
        )


@router.get("/yearly-expense-chart", response_model=ApiResponse[YearlyExpenseChartResponse])
async def get_yearly_expense_chart(
    year: Optional[int] = Query(None, description="年份，默认为当前年份"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取年度收支图表数据"""
    try:
        if year is None:
            year = datetime.now().year
        
        current_year = datetime.now().year
        if year < 2000 or year > current_year + 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"年份必须在2000到{current_year + 1}之间"
            )
        
        family_user_ids = await get_user_family_members(current_user, db)
        
        # 查询月度支出
        monthly_expense_data = db.query(
            func.extract('month', Bill.transaction_time).label('month'),
            func.sum(Bill.amount).label('total_amount')
        ).filter(
            Bill.user_id.in_(family_user_ids),
            Bill.transaction_type == "支出",
            func.extract('year', Bill.transaction_time) == year
        ).group_by(func.extract('month', Bill.transaction_time)).all()
        
        # 查询月度收入
        monthly_income_data = db.query(
            func.extract('month', Bill.transaction_time).label('month'),
            func.sum(Bill.amount).label('total_amount')
        ).filter(
            Bill.user_id.in_(family_user_ids),
            Bill.transaction_type == "收入",
            func.extract('year', Bill.transaction_time) == year
        ).group_by(func.extract('month', Bill.transaction_time)).all()

        month_names = {
            1: "1月", 2: "2月", 3: "3月", 4: "4月", 5: "5月", 6: "6月",
            7: "7月", 8: "8月", 9: "9月", 10: "10月", 11: "11月", 12: "12月"
        }
        
        monthly_expense_dict = {int(row.month): float(row.total_amount) for row in monthly_expense_data if row.total_amount is not None}
        monthly_income_dict = {int(row.month): float(row.total_amount) for row in monthly_income_data if row.total_amount is not None}
        
        monthly_items = []
        total_year_expense = 0.0
        total_year_income = 0.0
        
        for month in range(1, 13):
            expense_amount = monthly_expense_dict.get(month, 0.0)
            income_amount = monthly_income_dict.get(month, 0.0)
            
            total_year_expense += expense_amount
            total_year_income += income_amount
            
            monthly_items.append(MonthlyExpenseItem(
                month=month,
                month_name=month_names[month],
                amount=float(Decimal(str(expense_amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                income=float(Decimal(str(income_amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            ))
        
        total_year_expense = float(Decimal(str(total_year_expense)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        total_year_income = float(Decimal(str(total_year_income)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        
        chart_data = YearlyExpenseChartResponse(
            monthly_expenses=monthly_items,
            total_year_expense=total_year_expense,
            total_year_income=total_year_income
        )
        
        return ApiResponse[YearlyExpenseChartResponse](
            data=chart_data,
            success=True,
            message=f"获取{year}年度收支图表数据成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取年度收支图表数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取年度收支图表数据失败"
        )