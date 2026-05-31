from typing import Any, Dict, List, Optional, Sequence, Union

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from models.bill import BillCategory
from models.classification_rule import ClassificationRule
from schemas.classification_rule import ClassificationRuleCreate, ClassificationRuleUpdate


"""分类规则 CRUD 与 AI 提示词格式化。

分类规则不在后端做正则/关键词硬匹配，而是在 AI 自动分类时注入提示词供模型优先参考。
"""


VALID_SOURCE_TYPES = ("alipay", "jd", "cmb", "wechat", "meituan", "manual", "all")
VALID_TRANSACTION_TYPES = ("expense", "income", "transfer")
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
    "请优先参考以上用户自定义规则；规则为自然语言线索，请结合账单描述语义判断是否适用。"
    "优先级高的规则优先；无适用规则时再根据描述智能推断。"
)


def format_classification_rules_for_ai_prompt(
    rules: Sequence[Union[ClassificationRule, Dict[str, Any]]],
) -> str:
    """将分类规则格式化为注入 AI 提示词的文本。"""
    if not rules:
        return ""

    lines = ["\n分类规则（AI 分类时请优先参考，按优先级从高到低）："]
    for rule in rules:
        if isinstance(rule, dict):
            rule_text = rule["rule_text"]
            target_category = rule["target_category"]
            transaction_type = rule.get("transaction_type", "expense")
            source_type = rule.get("source_type", "all")
        else:
            rule_text = rule.rule_text
            target_category = rule.target_category
            transaction_type = rule.transaction_type
            source_type = rule.source_type

        type_label = TRANSACTION_TYPE_LABELS.get(transaction_type, transaction_type)
        source_label = SOURCE_TYPE_LABELS.get(source_type, source_type)
        lines.append(
            f"- 「{rule_text}」→ 分类「{target_category}」"
            f"（收支类型：{type_label}；来源：{source_label}）"
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
        "rule_text": rule.rule_text,
        "source_type": rule.source_type,
        "target_category": rule.target_category,
        "transaction_type": rule.transaction_type,
        "priority": rule.priority,
        "is_active": rule.is_active,
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


def list_classification_rules(
    db: Session,
    user_id: int,
    *,
    page: int = 1,
    page_size: int = 20,
    source_type: Optional[str] = None,
    target_category: Optional[str] = None,
    transaction_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
) -> Dict[str, Any]:
    query = db.query(ClassificationRule).filter(ClassificationRule.created_by == user_id)

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


def _find_duplicate_rule(
    db: Session,
    user_id: int,
    rule_text: str,
    source_type: str,
    transaction_type: str,
    exclude_id: Optional[int] = None,
) -> Optional[ClassificationRule]:
    query = db.query(ClassificationRule).filter(
        ClassificationRule.created_by == user_id,
        ClassificationRule.rule_text == rule_text,
        ClassificationRule.source_type == source_type,
        ClassificationRule.transaction_type == transaction_type,
    )
    if exclude_id is not None:
        query = query.filter(ClassificationRule.id != exclude_id)
    return query.first()


def create_classification_rule_record(
    db: Session,
    user_id: int,
    payload: ClassificationRuleCreate,
) -> ClassificationRule:
    existing = _find_duplicate_rule(
        db,
        user_id,
        payload.rule_text,
        payload.source_type,
        payload.transaction_type,
    )
    if existing:
        raise ValueError(f"相同的规则已存在 (ID: {existing.id})")

    _validate_target_category(db, payload.target_category, payload.transaction_type)

    rule = ClassificationRule(**payload.model_dump(), created_by=user_id)
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
    rule = (
        db.query(ClassificationRule)
        .filter(ClassificationRule.id == rule_id, ClassificationRule.created_by == user_id)
        .first()
    )
    if not rule:
        raise ValueError("分类规则不存在")

    update_data = payload.model_dump(exclude_unset=True)
    new_rule_text = update_data.get("rule_text", rule.rule_text)
    new_source_type = update_data.get("source_type", rule.source_type)
    new_transaction_type = update_data.get("transaction_type", rule.transaction_type)

    if {"rule_text", "source_type", "transaction_type"} & update_data.keys():
        existing = _find_duplicate_rule(
            db,
            user_id,
            new_rule_text,
            new_source_type,
            new_transaction_type,
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


def delete_classification_rule_record(db: Session, user_id: int, rule_id: int) -> None:
    rule = (
        db.query(ClassificationRule)
        .filter(ClassificationRule.id == rule_id, ClassificationRule.created_by == user_id)
        .first()
    )
    if not rule:
        raise ValueError("分类规则不存在")
    db.delete(rule)
    db.commit()
