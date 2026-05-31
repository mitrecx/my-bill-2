#!/usr/bin/env python3
"""分类规则管理脚本（CRUD + AI 提示词预览）。"""

import argparse
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "backend"))

from config.database import get_db
from models.bill import BillCategory
from models.classification_rule import ClassificationRule
from models import User
from services.classification_rule_service import format_classification_rules_for_ai_prompt


def _default_user_id(db):
    user = db.query(User).order_by(User.id).first()
    if not user:
        raise RuntimeError("数据库中无用户，无法创建规则")
    return user.id


def list_rules():
    print("=== 分类规则列表 ===")
    db = next(get_db())
    try:
        rules = db.query(ClassificationRule).order_by(
            ClassificationRule.priority.desc(),
            ClassificationRule.created_at.desc(),
        ).all()
        if not rules:
            print("暂无分类规则")
            return
        print(f"共 {len(rules)} 条规则:\n")
        for rule in rules:
            status = "✓" if rule.is_active else "✗"
            print(f"{status} ID: {rule.id}")
            print(f"   优先级: {rule.priority}")
            print(f"   来源: {rule.source_type}")
            print(f"   收支类型: {rule.transaction_type}")
            print(f"   目标分类: {rule.target_category}")
            print(f"   规则文本: {rule.rule_text}")
            print(f"   创建时间: {rule.created_at}")
            print()
    finally:
        db.close()


def add_rule(rule_text, source_type, target_category, transaction_type="expense", priority=5):
    print("=== 添加分类规则 ===")
    db = next(get_db())
    try:
        category = db.query(BillCategory).filter(
            BillCategory.category_name == target_category,
            BillCategory.is_deleted == False,
        ).first()
        if not category:
            print(f"错误: 分类 '{target_category}' 不存在")
            return

        user_id = _default_user_id(db)
        existing = db.query(ClassificationRule).filter(
            ClassificationRule.created_by == user_id,
            ClassificationRule.rule_text == rule_text,
            ClassificationRule.source_type == source_type,
            ClassificationRule.transaction_type == transaction_type,
        ).first()
        if existing:
            print(f"错误: 相同规则已存在 (ID: {existing.id})")
            return

        rule = ClassificationRule(
            rule_text=rule_text,
            source_type=source_type,
            target_category=target_category,
            transaction_type=transaction_type,
            priority=priority,
            is_active=True,
            created_by=user_id,
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
        print(f"成功创建规则 (ID: {rule.id})，归属用户 ID: {user_id}")
        print(format_classification_rules_for_ai_prompt([rule]))
    except Exception as exc:
        print(f"添加规则失败: {exc}")
    finally:
        db.close()


def delete_rule(rule_id):
    print("=== 删除分类规则 ===")
    db = next(get_db())
    try:
        rule = db.query(ClassificationRule).filter(ClassificationRule.id == rule_id).first()
        if not rule:
            print(f"错误: 规则 ID {rule_id} 不存在")
            return
        print(f"将删除: ID={rule.id} {rule.rule_text} → {rule.target_category}")
        confirm = input("确认删除? (y/N): ")
        if confirm.lower() == "y":
            db.delete(rule)
            db.commit()
            print("规则删除成功")
        else:
            print("取消删除")
    finally:
        db.close()


def toggle_rule(rule_id):
    print("=== 切换规则状态 ===")
    db = next(get_db())
    try:
        rule = db.query(ClassificationRule).filter(ClassificationRule.id == rule_id).first()
        if not rule:
            print(f"错误: 规则 ID {rule_id} 不存在")
            return
        rule.is_active = not rule.is_active
        db.commit()
        status = "启用" if rule.is_active else "禁用"
        print(f"规则 ID {rule_id} 已{status}")
    finally:
        db.close()


def preview_rule(rule_text, description, source_type="all", transaction_type="expense", target_category="示例分类"):
    print("=== AI 提示词预览（非程序匹配） ===")
    rule = ClassificationRule(
        rule_text=rule_text,
        source_type=source_type,
        target_category=target_category,
        transaction_type=transaction_type,
        priority=1,
        is_active=True,
    )
    print(format_classification_rules_for_ai_prompt([rule]))
    print(f"示例账单描述: {description}")
    print("说明: 实际分类由 AI 参考上述规则语义判断，后端不做正则/关键词硬匹配。")


def show_statistics():
    print("=== 分类规则统计 ===")
    db = next(get_db())
    try:
        total = db.query(ClassificationRule).count()
        active = db.query(ClassificationRule).filter(ClassificationRule.is_active == True).count()
        print(f"总规则数: {total}")
        print(f"启用规则数: {active}")
        print(f"禁用规则数: {total - active}")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="分类规则管理工具")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="列出所有分类规则")

    add_parser = subparsers.add_parser("add", help="添加分类规则")
    add_parser.add_argument("rule_text", help="规则文本（供 AI 参考）")
    add_parser.add_argument("source_type", help="来源类型")
    add_parser.add_argument("target_category", help="目标分类名称")
    add_parser.add_argument("--transaction-type", default="expense", choices=["expense", "income", "transfer"])
    add_parser.add_argument("--priority", type=int, default=5)

    delete_parser = subparsers.add_parser("delete", help="删除分类规则")
    delete_parser.add_argument("rule_id", type=int)

    toggle_parser = subparsers.add_parser("toggle", help="切换规则启用状态")
    toggle_parser.add_argument("rule_id", type=int)

    preview_parser = subparsers.add_parser("preview", help="预览规则在 AI 提示词中的呈现")
    preview_parser.add_argument("rule_text", help="规则文本")
    preview_parser.add_argument("description", help="示例账单描述")

    subparsers.add_parser("stats", help="显示统计信息")

    args = parser.parse_args()
    if args.command == "list":
        list_rules()
    elif args.command == "add":
        add_rule(args.rule_text, args.source_type, args.target_category, args.transaction_type, args.priority)
    elif args.command == "delete":
        delete_rule(args.rule_id)
    elif args.command == "toggle":
        toggle_rule(args.rule_id)
    elif args.command == "preview":
        preview_rule(args.rule_text, args.description)
    elif args.command == "stats":
        show_statistics()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
