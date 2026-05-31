from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from config.database import get_db
from models import User
from schemas import (
    ClassificationRuleCreate,
    ClassificationRuleUpdate,
    ClassificationRuleResponse,
    ClassificationRuleListResponse,
    ClassificationRuleBatchCreate,
)
from schemas.common import ApiResponse
from api.auth import get_current_user
from services.classification_rule_service import (
    create_classification_rule_record,
    delete_classification_rule_record,
    get_classification_rule_record,
    list_classification_rules,
    toggle_classification_rule_record,
    update_classification_rule_record,
)

router = APIRouter(prefix="/classification-rules", tags=["classification-rules"])


def _http_error(exc: Exception) -> HTTPException:
    message = str(exc)
    status_code = 404 if "不存在" in message else 400
    return HTTPException(status_code=status_code, detail=message)


@router.get("", response_model=ApiResponse[ClassificationRuleListResponse])
async def get_classification_rules(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    scope: Optional[str] = Query(None, description="按作用域筛选 personal/family"),
    source_type: Optional[str] = Query(None, description="按来源类型筛选"),
    target_category: Optional[str] = Query(None, description="按目标分类筛选"),
    transaction_type: Optional[str] = Query(None, description="按交易类型筛选 expense/income/transfer"),
    is_active: Optional[bool] = Query(None, description="按启用状态筛选"),
    search: Optional[str] = Query(None, description="搜索规则文本"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户可见的分类规则（个人规则 + 家庭规则）"""
    try:
        result = list_classification_rules(
            db,
            current_user.id,
            page=page,
            page_size=page_size,
            scope=scope,
            source_type=source_type,
            target_category=target_category,
            transaction_type=transaction_type,
            is_active=is_active,
            search=search,
        )
    except ValueError as exc:
        raise _http_error(exc) from exc

    data = ClassificationRuleListResponse(**result)
    return ApiResponse(success=True, data=data, message="获取分类规则列表成功")


@router.post("", response_model=ApiResponse[ClassificationRuleResponse])
async def create_classification_rule(
    rule_data: ClassificationRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建分类规则（personal 仅对自己生效，family 对家庭所有成员生效）"""
    try:
        rule = create_classification_rule_record(db, current_user.id, rule_data)
    except ValueError as exc:
        raise _http_error(exc) from exc
    return ApiResponse(success=True, data=rule, message="分类规则创建成功")


@router.post("/batch", response_model=ApiResponse[List[ClassificationRuleResponse]])
async def create_classification_rules_batch(
    batch_data: ClassificationRuleBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量创建分类规则"""
    created_rules = []
    errors = []

    for i, rule_data in enumerate(batch_data.rules):
        try:
            rule = create_classification_rule_record(db, current_user.id, rule_data)
            created_rules.append(rule)
        except ValueError as exc:
            errors.append(f"规则 {i + 1}: {exc}")

    if errors:
        raise HTTPException(status_code=400, detail="批量创建失败:\n" + "\n".join(errors))

    return ApiResponse(
        success=True,
        data=created_rules,
        message=f"成功创建 {len(created_rules)} 条分类规则",
    )


@router.get("/{rule_id}", response_model=ApiResponse[ClassificationRuleResponse])
async def get_classification_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单条分类规则"""
    try:
        rule = get_classification_rule_record(db, current_user.id, rule_id)
    except ValueError as exc:
        raise _http_error(exc) from exc
    return ApiResponse(success=True, data=rule, message="获取分类规则成功")


@router.put("/{rule_id}", response_model=ApiResponse[ClassificationRuleResponse])
async def update_classification_rule(
    rule_id: int,
    rule_data: ClassificationRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新分类规则"""
    try:
        rule = update_classification_rule_record(db, current_user.id, rule_id, rule_data)
    except ValueError as exc:
        raise _http_error(exc) from exc
    return ApiResponse(success=True, data=rule, message="分类规则更新成功")


@router.delete("/{rule_id}", response_model=ApiResponse[bool])
async def delete_classification_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除分类规则"""
    try:
        delete_classification_rule_record(db, current_user.id, rule_id)
    except ValueError as exc:
        raise _http_error(exc) from exc
    return ApiResponse(success=True, data=True, message="分类规则删除成功")


@router.patch("/{rule_id}/toggle", response_model=ApiResponse[ClassificationRuleResponse])
async def toggle_classification_rule_status(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """切换分类规则的启用状态"""
    try:
        rule = toggle_classification_rule_record(db, current_user.id, rule_id)
    except ValueError as exc:
        raise _http_error(exc) from exc
    return ApiResponse(success=True, data=rule, message="分类规则状态切换成功")


@router.get("/transaction-types/options")
async def get_transaction_type_options():
    """获取可用的交易类型选项"""
    data = {
        "transaction_types": [
            {"value": "expense", "label": "支出"},
            {"value": "income", "label": "收入"},
            {"value": "transfer", "label": "不计收支"},
        ]
    }
    return ApiResponse(success=True, data=data, message="获取交易类型选项成功")


@router.get("/source-types/options")
async def get_source_type_options():
    """获取可用的来源类型选项"""
    data = {
        "source_types": [
            {"value": "alipay", "label": "支付宝"},
            {"value": "jd", "label": "京东"},
            {"value": "cmb", "label": "招商银行"},
            {"value": "wechat", "label": "微信支付"},
            {"value": "meituan", "label": "美团"},
            {"value": "manual", "label": "手动录入"},
            {"value": "all", "label": "所有来源"},
        ]
    }
    return ApiResponse(success=True, data=data, message="获取来源类型选项成功")
