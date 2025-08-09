#!/usr/bin/env python3
"""
分类规则管理脚本
用于管理和维护分类规则
"""

import sys
import os
import argparse

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

from config.database import get_db
from models.bill import BillCategory
from models.classification_rule import ClassificationRule
from services.rule_classification_service import rule_classification_service


def list_rules():
    """列出所有分类规则"""
    print("=== 分类规则列表 ===")
    
    db = next(get_db())
    
    try:
        rules = db.query(ClassificationRule).order_by(
            ClassificationRule.priority.desc(),
            ClassificationRule.created_at.desc()
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
            print(f"   目标分类: {rule.target_category}")
            print(f"   规则: {rule.rule_text}")
            print(f"   创建时间: {rule.created_at}")
            print()
        
    except Exception as e:
        print(f"获取规则列表失败: {e}")
    finally:
        db.close()


def add_rule(rule_text, source_type, target_category, priority=5):
    """添加分类规则"""
    print(f"=== 添加分类规则 ===")
    
    db = next(get_db())
    
    try:
        # 检查目标分类是否存在
        category = db.query(BillCategory).filter(
            BillCategory.category_name == target_category
        ).first()
        
        if not category:
            print(f"错误: 分类 '{target_category}' 不存在")
            print("可用分类:")
            categories = db.query(BillCategory).all()
            for cat in categories:
                print(f"  - {cat.category_name} ({cat.category_type})")
            return
        
        # 检查是否已存在相同规则
        existing = db.query(ClassificationRule).filter(
            ClassificationRule.rule_text == rule_text,
            ClassificationRule.source_type == source_type
        ).first()
        
        if existing:
            print(f"错误: 相同规则已存在 (ID: {existing.id})")
            return
        
        # 创建规则
        rule = ClassificationRule(
            rule_text=rule_text,
            source_type=source_type,
            target_category=target_category,
            priority=priority,
            is_active=True
        )
        
        db.add(rule)
        db.commit()
        db.refresh(rule)
        
        print(f"成功创建规则 (ID: {rule.id})")
        print(f"  规则: {rule_text}")
        print(f"  来源: {source_type}")
        print(f"  目标分类: {target_category}")
        print(f"  优先级: {priority}")
        
    except Exception as e:
        print(f"添加规则失败: {e}")
    finally:
        db.close()


def delete_rule(rule_id):
    """删除分类规则"""
    print(f"=== 删除分类规则 ===")
    
    db = next(get_db())
    
    try:
        rule = db.query(ClassificationRule).filter(
            ClassificationRule.id == rule_id
        ).first()
        
        if not rule:
            print(f"错误: 规则 ID {rule_id} 不存在")
            return
        
        print(f"将删除规则:")
        print(f"  ID: {rule.id}")
        print(f"  规则: {rule.rule_text}")
        print(f"  来源: {rule.source_type}")
        print(f"  目标分类: {rule.target_category}")
        
        confirm = input("确认删除? (y/N): ")
        if confirm.lower() == 'y':
            db.delete(rule)
            db.commit()
            print("规则删除成功")
        else:
            print("取消删除")
        
    except Exception as e:
        print(f"删除规则失败: {e}")
    finally:
        db.close()


def toggle_rule(rule_id):
    """切换规则启用状态"""
    print(f"=== 切换规则状态 ===")
    
    db = next(get_db())
    
    try:
        rule = db.query(ClassificationRule).filter(
            ClassificationRule.id == rule_id
        ).first()
        
        if not rule:
            print(f"错误: 规则 ID {rule_id} 不存在")
            return
        
        old_status = "启用" if rule.is_active else "禁用"
        rule.is_active = not rule.is_active
        new_status = "启用" if rule.is_active else "禁用"
        
        db.commit()
        
        print(f"规则 ID {rule_id} 状态已从 '{old_status}' 切换为 '{new_status}'")
        
    except Exception as e:
        print(f"切换规则状态失败: {e}")
    finally:
        db.close()


def test_rule(rule_text, description):
    """测试规则匹配"""
    print(f"=== 测试规则匹配 ===")
    
    db = next(get_db())
    
    try:
        # 创建临时规则对象
        rule = ClassificationRule(
            rule_text=rule_text,
            source_type='all',
            target_category='测试分类',
            priority=1,
            is_active=True
        )
        
        # 测试匹配
        service = rule_classification_service
        matches = service._match_simple_keyword(rule_text, description)
        
        print(f"规则: {rule_text}")
        print(f"描述: {description}")
        print(f"匹配结果: {'✓ 匹配' if matches else '✗ 不匹配'}")
        
        # 测试不同格式
        if service._is_keyword_rule(rule_text):
            matches = service._match_keyword_rule(rule_text, description)
            print(f"关键词匹配: {'✓ 匹配' if matches else '✗ 不匹配'}")
        
        if service._is_regex_rule(rule_text):
            matches = service._match_regex_rule(rule_text, description)
            print(f"正则匹配: {'✓ 匹配' if matches else '✗ 不匹配'}")
        
    except Exception as e:
        print(f"测试规则失败: {e}")
    finally:
        db.close()


def show_statistics():
    """显示统计信息"""
    print("=== 分类规则统计 ===")
    
    db = next(get_db())
    
    try:
        stats = rule_classification_service.get_rule_statistics(db)
        
        print(f"总规则数: {stats.get('total_rules', 0)}")
        print(f"启用规则数: {stats.get('active_rules', 0)}")
        print(f"禁用规则数: {stats.get('inactive_rules', 0)}")
        
        source_stats = stats.get('source_stats', {})
        print("\n按来源类型统计:")
        for source_type, count in source_stats.items():
            source_name = {
                'alipay': '支付宝',
                'jd': '京东',
                'cmb': '招商银行',
                'all': '所有来源'
            }.get(source_type, source_type)
            print(f"  {source_name}: {count} 条规则")
        
    except Exception as e:
        print(f"获取统计信息失败: {e}")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description='分类规则管理工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 列出规则
    subparsers.add_parser('list', help='列出所有分类规则')
    
    # 添加规则
    add_parser = subparsers.add_parser('add', help='添加分类规则')
    add_parser.add_argument('rule_text', help='规则文本')
    add_parser.add_argument('source_type', choices=['alipay', 'jd', 'cmb', 'all'], help='来源类型')
    add_parser.add_argument('target_category', help='目标分类')
    add_parser.add_argument('--priority', type=int, default=5, help='优先级 (默认: 5)')
    
    # 删除规则
    delete_parser = subparsers.add_parser('delete', help='删除分类规则')
    delete_parser.add_argument('rule_id', type=int, help='规则ID')
    
    # 切换规则状态
    toggle_parser = subparsers.add_parser('toggle', help='切换规则启用状态')
    toggle_parser.add_argument('rule_id', type=int, help='规则ID')
    
    # 测试规则
    test_parser = subparsers.add_parser('test', help='测试规则匹配')
    test_parser.add_argument('rule_text', help='规则文本')
    test_parser.add_argument('description', help='账单描述')
    
    # 统计信息
    subparsers.add_parser('stats', help='显示统计信息')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        list_rules()
    elif args.command == 'add':
        add_rule(args.rule_text, args.source_type, args.target_category, args.priority)
    elif args.command == 'delete':
        delete_rule(args.rule_id)
    elif args.command == 'toggle':
        toggle_rule(args.rule_id)
    elif args.command == 'test':
        test_rule(args.rule_text, args.description)
    elif args.command == 'stats':
        show_statistics()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()