from typing import Any, Dict, List, Optional, Sequence, Union

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session

from models.bill import BillCategory
from models.classification_rule import ClassificationRule
from models.family import FamilyMember
from schemas.classification_rule import ClassificationRuleCreate, ClassificationRuleUpdate


"""分类规则 CRUD 与 AI 提示词格式化。

支持 personal（仅创建者）与 family（家庭共享）两种作用域。
不在后端做正则/关键词硬匹配，而是在 AI 自动分类时注入提示词供模型优先参考。
"""


VALID_SOURCE_TYPES = ("alipay", "jd", "cmb", "wechat", "meituan", "manual", "all")
VALID_TRANSACTION_TYPES = ("expense", "income", "transfer")
VALID_SCOPES = ("personal", "family")
CN_TO_TRANSACTION_TYPE = {
    "支出": "expense",
    "收入": "income",
    "不计收支": "transfer",
}
TRANSACTION_TYPE_LABELS = {
    "expense": "支出",
    "income": "收入",
    "transfer": "不计收支",
}
SCOPE_LABELS = {
    "personal": "个人",
    "family": "家庭",
}
SOURCE_TYPE_LABELS = {
    "alipay": "支付宝",
    "jd": "京东",
    "cmb": "招商银行",
    "wechat": "微信支付",
    "meituan": "美团",
    "manual": "手动录入",
    "all": "所有来源",
}
CLASSIFICATION_RULES_AI_GUIDANCE = (
    "请优先参考以上个人与家庭自定义规则；规则为自然语言线索，请结合账单描述语义判断是否适用。"
    "优先级高的规则优先；无适用规则时再根据描述智能推断。"
)


def get_user_family_id(db: Session, user_id: int) -> Optional[int]:
    member = db.query(FamilyMember).filter(FamilyMember.user_id == user_id).first()
    return member.family_id if member else None


def applicable_rules_filter(db: Session, user_id: int):
    """当前用户 AI 分类时可用的规则：个人规则 + 所在家庭的家庭规则。"""
    personal = and_(
        ClassificationRule.scope == "personal",
        ClassificationRule.created_by == user_id,
    )
    family_id = get_user_family_id(db, user_id)
    if family_id is None:
        return personal
    return or_(
        personal,
        and_(
            ClassificationRule.scope == "family",
            ClassificationRule.family_id == family_id,
        ),
    )


def visible_rules_filter(db: Session, user_id: int):
    """列表可见规则：与 AI 适用规则相同。"""
    return applicable_rules_filter(db, user_id)


def format_classification_rules_for_ai_prompt(
    rules: Sequence[Union[ClassificationRule, Dict[str, Any]]],
) -> str:
    if not rules:
        return ""

    lines = ["\n分类规则（AI 分类时请优先参考，按优先级从高到低）："]
    for rule in rules:
        if isinstance(rule, dict):
            rule_text = rule["rule_text"]
            target_category = rule["target_category"]
            transaction_type = rule.get("transaction_type", "expense")
            source_type = rule.get("source_type", "all")
            scope = rule.get("scope", "personal")
        else:
            rule_text = rule.rule_text
            target_category = rule.target_category
            transaction_type = rule.transaction_type
            source_type = rule.source_type
            scope = rule.scope

        type_label = TRANSACTION_TYPE_LABELS.get(transaction_type, transaction_type)
        source_label = SOURCE_TYPE_LABELS.get(source_type, source_type)
        scope_label = SCOPE_LABELS.get(scope, scope)
        lines.append(
            f"- 「{rule_text}」→ 分类「{target_category}」"
            f"（作用域：{scope_label}；收支类型：{type_label}；来源：{source_label}）"
        )

    lines.append(f"\n{CLASSIFICATION_RULES_AI_GUIDANCE}\n")
    return "\n".join(lines)


def normalize_transaction_type(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    normalized = value.strip()
    if normalized in VALID_TRANSACTION_TYPES:
        return normalized
    return CN_TO_TRANSACTION_TYPE.get(normalized, normalized)


def serialize_classification_rule(rule: ClassificationRule) -> Dict[str, Any]:
    return {
        "id": rule.id,
        "scope": rule.scope,
        "family_id": rule.family_id,
        "rule_text": rule.rule_text,
        "source_type": rule.source_type,
        "target_category": rule.target_category,
        "transaction_type": rule.transaction_type,
        "priority": rule.priority,
        "is_active": rule.is_active,
        "created_by": rule.created_by,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
        "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
    }


def _validate_target_category(
    db: Session,
    category_name: str,
    transaction_type: str = "expense",
) -> None:
    category = (
        db.query(BillCategory)
        .filter(BillCategory.category_name == category_name, BillCategory.is_deleted == False)
        .first()
    )
    if not category:
        raise ValueError("目标分类不存在或已被删除")

    if transaction_type == "expense" and category.category_type != "expense":
        raise ValueError("支出规则的目标分类必须是支出类分类")
    if transaction_type == "income" and category.category_type != "income":
        raise ValueError("收入规则的目标分类必须是收入类分类")


def _validate_scope_payload(scope: str, family_id: Optional[int]) -> None:
    if scope not in VALID_SCOPES:
        raise ValueError(f"scope 无效，可选: {', '.join(VALID_SCOPES)}")
    if scope == "family" and family_id is None:
        raise ValueError("家庭级规则需要加入家庭后才能创建")
    if scope == "personal" and family_id is not None:
        raise ValueError("个人级规则不能设置 family_id")


def _get_accessible_rule(db: Session, user_id: int, rule_id: int) -> ClassificationRule:
    rule = db.query(ClassificationRule).filter(ClassificationRule.id == rule_id).first()
    if not rule:
        raise ValueError("分类规则不存在")

    if rule.scope == "personal":
        if rule.created_by != user_id:
            raise ValueError("分类规则不存在")
        return rule

    family_id = get_user_family_id(db, user_id)
    if family_id is None or rule.family_id != family_id:
        raise ValueError("分类规则不存在")
    return rule


def _can_modify_rule(rule: ClassificationRule, user_id: int, family_id: Optional[int]) -> bool:
    if rule.scope == "personal":
        return rule.created_by == user_id
    return family_id is not None and rule.family_id == family_id


def _find_duplicate_rule(
    db: Session,
    *,
    scope: str,
    user_id: int,
    family_id: Optional[int],
    rule_text: str,
    source_type: str,
    transaction_type: str,
    exclude_id: Optional[int] = None,
) -> Optional[ClassificationRule]:
    if scope == "personal":
        query = db.query(ClassificationRule).filter(
            ClassificationRule.scope == "personal",
            ClassificationRule.created_by == user_id,
            ClassificationRule.rule_text == rule_text,
            ClassificationRule.source_type == source_type,
            ClassificationRule.transaction_type == transaction_type,
        )
    else:
        query = db.query(ClassificationRule).filter(
            ClassificationRule.scope == "family",
            ClassificationRule.family_id == family_id,
            ClassificationRule.rule_text == rule_text,
            ClassificationRule.source_type == source_type,
            ClassificationRule.transaction_type == transaction_type,
        )
    if exclude_id is not None:
        query = query.filter(ClassificationRule.id != exclude_id)
    return query.first()


def _resolve_scope_fields(
    db: Session,
    user_id: int,
    scope: str,
) -> tuple[str, Optional[int]]:
    if scope == "personal":
        return "personal", None
    family_id = get_user_family_id(db, user_id)
    if family_id is None:
        raise ValueError("用户未加入家庭，无法创建家庭级规则")
    return "family", family_id


def query_applicable_active_rules(
    db: Session,
    user_id: int,
    *,
    source_type: Optional[str] = None,
    source_types: Optional[Sequence[str]] = None,
    transaction_type: Optional[str] = None,
    transaction_types: Optional[Sequence[str]] = None,
) -> List[ClassificationRule]:
    """查询用户 AI 分类时可用的启用规则。"""
    query = db.query(ClassificationRule).filter(
        applicable_rules_filter(db, user_id),
        ClassificationRule.is_active == True,
    )

    if source_types:
        query = query.filter(
            ClassificationRule.source_type.in_(source_types)
            | (ClassificationRule.source_type == "all")
        )
    elif source_type:
        query = query.filter(
            (ClassificationRule.source_type == source_type)
            | (ClassificationRule.source_type == "all")
        )
    else:
        query = query.filter(ClassificationRule.source_type == "all")

    normalized_types = set()
    if transaction_types:
        for tt in transaction_types:
            normalized = normalize_transaction_type(tt)
            if normalized:
                normalized_types.add(normalized)
    elif transaction_type:
        normalized = normalize_transaction_type(transaction_type)
        if normalized:
            normalized_types.add(normalized)

    if normalized_types:
        query = query.filter(ClassificationRule.transaction_type.in_(normalized_types))

    return query.order_by(desc(ClassificationRule.priority)).all()


def list_classification_rules(
    db: Session,
    user_id: int,
    *,
    page: int = 1,
    page_size: int = 20,
    scope: Optional[str] = None,
    source_type: Optional[str] = None,
    target_category: Optional[str] = None,
    transaction_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
) -> Dict[str, Any]:
    query = db.query(ClassificationRule).filter(visible_rules_filter(db, user_id))

    if scope:
        if scope not in VALID_SCOPES:
            raise ValueError(f"scope 无效，可选: {', '.join(VALID_SCOPES)}")
        query = query.filter(ClassificationRule.scope == scope)
    if source_type:
        if source_type not in VALID_SOURCE_TYPES:
            raise ValueError(f"source_type 无效，可选: {', '.join(VALID_SOURCE_TYPES)}")
        query = query.filter(ClassificationRule.source_type == source_type)
    if target_category:
        query = query.filter(ClassificationRule.target_category == target_category)
    if transaction_type:
        normalized = normalize_transaction_type(transaction_type)
        if normalized not in VALID_TRANSACTION_TYPES:
            raise ValueError(
                f"transaction_type 无效，可选: {', '.join(VALID_TRANSACTION_TYPES)}"
            )
        query = query.filter(ClassificationRule.transaction_type == normalized)
    if is_active is not None:
        query = query.filter(ClassificationRule.is_active == is_active)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                ClassificationRule.rule_text.ilike(pattern),
                ClassificationRule.target_category.ilike(pattern),
            )
        )

    query = query.order_by(desc(ClassificationRule.priority), desc(ClassificationRule.created_at))
    total = query.count()
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    rules = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "rules": [serialize_classification_rule(rule) for rule in rules],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_classification_rule_record(db: Session, user_id: int, rule_id: int) -> ClassificationRule:
    return _get_accessible_rule(db, user_id, rule_id)


def create_classification_rule_record(
    db: Session,
    user_id: int,
    payload: ClassificationRuleCreate,
) -> ClassificationRule:
    scope, family_id = _resolve_scope_fields(db, user_id, payload.scope)
    _validate_scope_payload(scope, family_id)

    existing = _find_duplicate_rule(
        db,
        scope=scope,
        user_id=user_id,
        family_id=family_id,
        rule_text=payload.rule_text,
        source_type=payload.source_type,
        transaction_type=payload.transaction_type,
    )
    if existing:
        raise ValueError(f"相同的规则已存在 (ID: {existing.id})")

    _validate_target_category(db, payload.target_category, payload.transaction_type)

    rule = ClassificationRule(
        **payload.model_dump(),
        scope=scope,
        family_id=family_id,
        created_by=user_id,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update_classification_rule_record(
    db: Session,
    user_id: int,
    rule_id: int,
    payload: ClassificationRuleUpdate,
) -> ClassificationRule:
    rule = _get_accessible_rule(db, user_id, rule_id)
    family_id = get_user_family_id(db, user_id)
    if not _can_modify_rule(rule, user_id, family_id):
        raise ValueError("无权修改该分类规则")

    update_data = payload.model_dump(exclude_unset=True)
    new_scope = update_data.get("scope", rule.scope)
    if new_scope != rule.scope:
        new_scope, new_family_id = _resolve_scope_fields(db, user_id, new_scope)
        update_data["scope"] = new_scope
        update_data["family_id"] = new_family_id
    else:
        new_scope = rule.scope
        new_family_id = rule.family_id

    new_rule_text = update_data.get("rule_text", rule.rule_text)
    new_source_type = update_data.get("source_type", rule.source_type)
    new_transaction_type = update_data.get("transaction_type", rule.transaction_type)

    if {"rule_text", "source_type", "transaction_type", "scope"} & update_data.keys():
        existing = _find_duplicate_rule(
            db,
            scope=new_scope,
            user_id=user_id if new_scope == "personal" else rule.created_by,
            family_id=new_family_id,
            rule_text=new_rule_text,
            source_type=new_source_type,
            transaction_type=new_transaction_type,
            exclude_id=rule_id,
        )
        if existing:
            raise ValueError(f"相同的规则已存在 (ID: {existing.id})")

    new_target_category = update_data.get("target_category", rule.target_category)
    if new_target_category:
        _validate_target_category(db, new_target_category, new_transaction_type)

    for field, value in update_data.items():
        setattr(rule, field, value)

    db.commit()
    db.refresh(rule)
    return rule


def toggle_classification_rule_record(db: Session, user_id: int, rule_id: int) -> ClassificationRule:
    rule = _get_accessible_rule(db, user_id, rule_id)
    family_id = get_user_family_id(db, user_id)
    if not _can_modify_rule(rule, user_id, family_id):
        raise ValueError("无权修改该分类规则")

    if not rule.is_active:
        _validate_target_category(db, rule.target_category, rule.transaction_type)

    rule.is_active = not rule.is_active
    db.commit()
    db.refresh(rule)
    return rule


def delete_classification_rule_record(db: Session, user_id: int, rule_id: int) -> None:
    rule = _get_accessible_rule(db, user_id, rule_id)
    family_id = get_user_family_id(db, user_id)
    if not _can_modify_rule(rule, user_id, family_id):
        raise ValueError("无权删除该分类规则")
    db.delete(rule)
    db.commit()
