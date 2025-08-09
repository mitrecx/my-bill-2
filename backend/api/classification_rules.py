from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from config.database import get_db
from models import ClassificationRule, User
from schemas import (
    ClassificationRuleCreate,
    ClassificationRuleUpdate,
    ClassificationRuleResponse,
    ClassificationRuleListResponse,
    ClassificationRuleBatchCreate,
    ClassificationRuleTestRequest,
    ClassificationRuleTestResponse
)
from schemas.common import ApiResponse
from api.auth import get_current_user

router = APIRouter(prefix="/classification-rules", tags=["classification-rules"])


@router.get("/", response_model=ApiResponse[ClassificationRuleListResponse])
async def get_classification_rules(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    source_type: Optional[str] = Query(None, description="按来源类型筛选"),
    target_category: Optional[str] = Query(None, description="按目标分类筛选"),
    is_active: Optional[bool] = Query(None, description="按启用状态筛选"),
    search: Optional[str] = Query(None, description="搜索规则文本"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取分类规则列表"""
    
    # 构建查询
    query = db.query(ClassificationRule)
    
    # 应用筛选条件
    if source_type:
        query = query.filter(ClassificationRule.source_type == source_type)
    
    if target_category:
        query = query.filter(ClassificationRule.target_category == target_category)
    
    if is_active is not None:
        query = query.filter(ClassificationRule.is_active == is_active)
    
    if search:
        query = query.filter(
            or_(
                ClassificationRule.rule_text.ilike(f"%{search}%"),
                ClassificationRule.target_category.ilike(f"%{search}%")
            )
        )
    
    # 按优先级和创建时间排序
    query = query.order_by(desc(ClassificationRule.priority), desc(ClassificationRule.created_at))
    
    # 获取总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    rules = query.offset(offset).limit(page_size).all()
    
    data = ClassificationRuleListResponse(
        rules=rules,
        total=total,
        page=page,
        page_size=page_size
    )
    
    return ApiResponse(success=True, data=data, message="获取分类规则列表成功")


@router.post("/", response_model=ApiResponse[ClassificationRuleResponse])
async def create_classification_rule(
    rule_data: ClassificationRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建分类规则"""
    
    # 检查是否已存在相同的规则
    existing_rule = db.query(ClassificationRule).filter(
        and_(
            ClassificationRule.rule_text == rule_data.rule_text,
            ClassificationRule.source_type == rule_data.source_type
        )
    ).first()
    
    if existing_rule:
        raise HTTPException(
            status_code=400,
            detail=f"相同的规则已存在 (ID: {existing_rule.id})"
        )
    
    # 创建新规则
    rule = ClassificationRule(
        **rule_data.dict(),
        created_by=current_user.id
    )
    
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    return ApiResponse(success=True, data=rule, message="分类规则创建成功")


@router.post("/batch", response_model=ApiResponse[List[ClassificationRuleResponse]])
async def create_classification_rules_batch(
    batch_data: ClassificationRuleBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量创建分类规则"""
    
    created_rules = []
    errors = []
    
    for i, rule_data in enumerate(batch_data.rules):
        try:
            # 检查是否已存在相同的规则
            existing_rule = db.query(ClassificationRule).filter(
                and_(
                    ClassificationRule.rule_text == rule_data.rule_text,
                    ClassificationRule.source_type == rule_data.source_type
                )
            ).first()
            
            if existing_rule:
                errors.append(f"规则 {i+1}: 相同的规则已存在 (ID: {existing_rule.id})")
                continue
            
            # 创建新规则
            rule = ClassificationRule(
                **rule_data.dict(),
                created_by=current_user.id
            )
            
            db.add(rule)
            db.flush()  # 获取ID但不提交
            created_rules.append(rule)
            
        except Exception as e:
            errors.append(f"规则 {i+1}: {str(e)}")
    
    if errors:
        db.rollback()
        error_message = "批量创建失败:\n" + "\n".join(errors)
        raise HTTPException(
            status_code=400,
            detail=error_message
        )
    
    db.commit()
    
    # 刷新所有创建的规则
    for rule in created_rules:
        db.refresh(rule)
    
    return ApiResponse(success=True, data=created_rules, message=f"成功创建 {len(created_rules)} 条分类规则")


@router.get("/{rule_id}", response_model=ApiResponse[ClassificationRuleResponse])
async def get_classification_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个分类规则"""
    
    rule = db.query(ClassificationRule).filter(ClassificationRule.id == rule_id).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="分类规则不存在")
    
    return ApiResponse(success=True, data=rule, message="获取分类规则成功")


@router.put("/{rule_id}", response_model=ApiResponse[ClassificationRuleResponse])
async def update_classification_rule(
    rule_id: int,
    rule_data: ClassificationRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新分类规则"""
    
    rule = db.query(ClassificationRule).filter(ClassificationRule.id == rule_id).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="分类规则不存在")
    
    # 如果更新了规则文本或来源类型，检查是否与其他规则冲突
    if rule_data.rule_text or rule_data.source_type:
        new_rule_text = rule_data.rule_text or rule.rule_text
        new_source_type = rule_data.source_type or rule.source_type
        
        existing_rule = db.query(ClassificationRule).filter(
            and_(
                ClassificationRule.rule_text == new_rule_text,
                ClassificationRule.source_type == new_source_type,
                ClassificationRule.id != rule_id
            )
        ).first()
        
        if existing_rule:
            raise HTTPException(
                status_code=400,
                detail=f"相同的规则已存在 (ID: {existing_rule.id})"
            )
    
    # 更新规则
    update_data = rule_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
    
    db.commit()
    db.refresh(rule)
    
    return ApiResponse(success=True, data=rule, message="分类规则更新成功")


@router.delete("/{rule_id}", response_model=ApiResponse[bool])
async def delete_classification_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除分类规则"""
    
    rule = db.query(ClassificationRule).filter(ClassificationRule.id == rule_id).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="分类规则不存在")
    
    db.delete(rule)
    db.commit()
    
    return ApiResponse(success=True, data=True, message="分类规则删除成功")


@router.patch("/{rule_id}/toggle", response_model=ApiResponse[ClassificationRuleResponse])
async def toggle_classification_rule_status(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """切换分类规则的启用状态"""
    
    rule = db.query(ClassificationRule).filter(ClassificationRule.id == rule_id).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="分类规则不存在")
    
    # 切换状态
    rule.is_active = not rule.is_active
    
    db.commit()
    db.refresh(rule)
    
    return ApiResponse(success=True, data=rule, message="分类规则状态切换成功")


@router.get("/source-types/options")
async def get_source_type_options():
    """获取可用的来源类型选项"""
    data = {
        "source_types": [
            {"value": "alipay", "label": "支付宝"},
            {"value": "jd", "label": "京东"},
            {"value": "cmb", "label": "招商银行"},
            {"value": "all", "label": "所有来源"}
        ]
    }
    return ApiResponse(success=True, data=data, message="获取来源类型选项成功")