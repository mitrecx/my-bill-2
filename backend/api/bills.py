from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, date
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
    BillUpdate
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bills", tags=["bills"])


async def get_user_families(user: User, db: Session) -> List[int]:
    """获取用户所属的家庭ID列表"""
    family_members = db.query(FamilyMember).filter(
        FamilyMember.user_id == user.id
    ).all()
    return [fm.family_id for fm in family_members]


@router.get("/", response_model=BillListResponse)
async def get_bills(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    family_id: Optional[int] = Query(None, description="家庭ID筛选"),
    category_id: Optional[int] = Query(None, description="分类ID筛选"),
    transaction_type: Optional[str] = Query(None, description="交易类型筛选"),
    source_type: Optional[str] = Query(None, description="来源类型筛选"),
    merchant_name: Optional[str] = Query(None, description="商户名称筛选"),
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
        # 获取用户所属家庭
        user_family_ids = await get_user_families(current_user, db)
        if not user_family_ids:
            return BillListResponse(
                bills=[],
                total=0,
                page=page,
                size=size,
                pages=0
            )
        
        # 构建查询
        query = db.query(Bill).options(
            joinedload(Bill.category),
            joinedload(Bill.family),
            joinedload(Bill.user)
        ).filter(Bill.family_id.in_(user_family_ids))
        
        # 应用筛选条件
        if family_id and family_id in user_family_ids:
            query = query.filter(Bill.family_id == family_id)
        
        if category_id:
            query = query.filter(Bill.category_id == category_id)
        
        if transaction_type:
            query = query.filter(Bill.transaction_type == transaction_type)
        
        if source_type:
            query = query.filter(Bill.source_type == source_type)
        
        if merchant_name:
            query = query.filter(Bill.merchant_name.ilike(f"%{merchant_name}%"))
        
        if start_date:
            query = query.filter(Bill.transaction_time >= start_date)
        
        if end_date:
            # 结束日期包含当天，所以加1天
            query = query.filter(Bill.transaction_time < end_date.replace(day=end_date.day + 1))
        
        if min_amount is not None:
            query = query.filter(Bill.amount >= min_amount)
        
        if max_amount is not None:
            query = query.filter(Bill.amount <= max_amount)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Bill.merchant_name.ilike(search_term),
                    Bill.description.ilike(search_term),
                    Bill.notes.ilike(search_term)
                )
            )
        
        # 排序
        if hasattr(Bill, sort_by):
            order_column = getattr(Bill, sort_by)
            if sort_order == "desc":
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(order_column)
        else:
            query = query.order_by(desc(Bill.transaction_time))
        
        # 分页
        total = query.count()
        offset = (page - 1) * size
        bills = query.offset(offset).limit(size).all()
        
        # 计算总页数
        pages = (total + size - 1) // size
        
        return BillListResponse(
            bills=[BillResponse.from_orm(bill) for bill in bills],
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"获取账单列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取账单列表失败"
        )


@router.get("/stats", response_model=BillStatsResponse)
async def get_bill_stats(
    family_id: Optional[int] = Query(None, description="家庭ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取账单统计信息"""
    try:
        # 获取用户所属家庭
        user_family_ids = await get_user_families(current_user, db)
        if not user_family_ids:
            return BillStatsResponse(
                total_income=0.0,
                total_expense=0.0,
                total_count=0,
                income_count=0,
                expense_count=0,
                avg_amount=0.0,
                by_category={},
                by_source={},
                by_month={}
            )
        
        # 构建基础查询
        query = db.query(Bill).filter(Bill.family_id.in_(user_family_ids))
        
        # 应用筛选条件
        if family_id and family_id in user_family_ids:
            query = query.filter(Bill.family_id == family_id)
        
        if start_date:
            query = query.filter(Bill.transaction_time >= start_date)
        
        if end_date:
            query = query.filter(Bill.transaction_time < end_date.replace(day=end_date.day + 1))
        
        # 基础统计
        bills = query.all()
        
        total_income = sum(bill.amount for bill in bills if bill.transaction_type == "收入")
        total_expense = sum(bill.amount for bill in bills if bill.transaction_type == "支出")
        total_count = len(bills)
        income_count = sum(1 for bill in bills if bill.transaction_type == "收入")
        expense_count = sum(1 for bill in bills if bill.transaction_type == "支出")
        avg_amount = sum(bill.amount for bill in bills) / total_count if total_count > 0 else 0
        
        # 按分类统计
        by_category = {}
        category_stats = db.query(
            BillCategory.category_name,
            Bill.transaction_type,
            func.sum(Bill.amount).label("total_amount"),
            func.count(Bill.id).label("count")
        ).join(Bill, Bill.category_id == BillCategory.id)\
         .filter(Bill.family_id.in_(user_family_ids))
        
        if family_id and family_id in user_family_ids:
            category_stats = category_stats.filter(Bill.family_id == family_id)
        if start_date:
            category_stats = category_stats.filter(Bill.transaction_time >= start_date)
        if end_date:
            category_stats = category_stats.filter(Bill.transaction_time < end_date.replace(day=end_date.day + 1))
        
        category_stats = category_stats.group_by(BillCategory.category_name, Bill.transaction_type).all()
        
        for stat in category_stats:
            category_name = stat.category_name
            if category_name not in by_category:
                by_category[category_name] = {"收入": 0, "支出": 0, "count": 0}
            
            by_category[category_name][stat.transaction_type] = float(stat.total_amount)
            by_category[category_name]["count"] += stat.count
        
        # 按来源统计
        by_source = {}
        source_stats = db.query(
            Bill.source_type,
            Bill.transaction_type,
            func.sum(Bill.amount).label("total_amount"),
            func.count(Bill.id).label("count")
        ).filter(Bill.family_id.in_(user_family_ids))
        
        if family_id and family_id in user_family_ids:
            source_stats = source_stats.filter(Bill.family_id == family_id)
        if start_date:
            source_stats = source_stats.filter(Bill.transaction_time >= start_date)
        if end_date:
            source_stats = source_stats.filter(Bill.transaction_time < end_date.replace(day=end_date.day + 1))
        
        source_stats = source_stats.group_by(Bill.source_type, Bill.transaction_type).all()
        
        for stat in source_stats:
            source_type = stat.source_type
            if source_type not in by_source:
                by_source[source_type] = {"收入": 0, "支出": 0, "count": 0}
            
            by_source[source_type][stat.transaction_type] = float(stat.total_amount)
            by_source[source_type]["count"] += stat.count
        
        # 按月统计
        by_month = {}
        month_stats = db.query(
            func.date_trunc('month', Bill.transaction_time).label("month"),
            Bill.transaction_type,
            func.sum(Bill.amount).label("total_amount"),
            func.count(Bill.id).label("count")
        ).filter(Bill.family_id.in_(user_family_ids))
        
        if family_id and family_id in user_family_ids:
            month_stats = month_stats.filter(Bill.family_id == family_id)
        if start_date:
            month_stats = month_stats.filter(Bill.transaction_time >= start_date)
        if end_date:
            month_stats = month_stats.filter(Bill.transaction_time < end_date.replace(day=end_date.day + 1))
        
        month_stats = month_stats.group_by(
            func.date_trunc('month', Bill.transaction_time),
            Bill.transaction_type
        ).order_by(func.date_trunc('month', Bill.transaction_time)).all()
        
        for stat in month_stats:
            month_key = stat.month.strftime("%Y-%m")
            if month_key not in by_month:
                by_month[month_key] = {"收入": 0, "支出": 0, "count": 0}
            
            by_month[month_key][stat.transaction_type] = float(stat.total_amount)
            by_month[month_key]["count"] += stat.count
        
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
        
    except Exception as e:
        logger.error(f"获取账单统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取账单统计失败"
        )


@router.get("/{bill_id}", response_model=BillResponse)
async def get_bill(
    bill_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个账单详情"""
    try:
        # 获取用户所属家庭
        user_family_ids = await get_user_families(current_user, db)
        
        bill = db.query(Bill).options(
            joinedload(Bill.category),
            joinedload(Bill.family),
            joinedload(Bill.user)
        ).filter(
            Bill.id == bill_id,
            Bill.family_id.in_(user_family_ids)
        ).first()
        
        if not bill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="账单不存在或无权访问"
            )
        
        return BillResponse.from_orm(bill)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取账单详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取账单详情失败"
        )


@router.put("/{bill_id}", response_model=BillResponse)
async def update_bill(
    bill_id: int,
    bill_update: BillUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新账单信息"""
    try:
        # 获取用户所属家庭
        user_family_ids = await get_user_families(current_user, db)
        
        bill = db.query(Bill).filter(
            Bill.id == bill_id,
            Bill.family_id.in_(user_family_ids)
        ).first()
        
        if not bill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="账单不存在或无权访问"
            )
        
        # 更新字段
        update_data = bill_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(bill, field, value)
        
        bill.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(bill)
        
        return BillResponse.from_orm(bill)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新账单失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新账单失败"
        )


@router.delete("/{bill_id}")
async def delete_bill(
    bill_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除账单"""
    try:
        # 获取用户所属家庭
        user_family_ids = await get_user_families(current_user, db)
        
        bill = db.query(Bill).filter(
            Bill.id == bill_id,
            Bill.family_id.in_(user_family_ids)
        ).first()
        
        if not bill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="账单不存在或无权访问"
            )
        
        db.delete(bill)
        db.commit()
        
        return {"message": "账单删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除账单失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除账单失败"
        )