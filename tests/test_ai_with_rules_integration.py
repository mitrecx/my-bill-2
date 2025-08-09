#!/usr/bin/env python3
"""
测试AI分类服务集成分类规则功能
验证分类规则是否正确集成到AI提示词中
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

from config.database import get_db
from models.bill import BillCategory
from models.classification_rule import ClassificationRule
from services.ai_classification_service import AIClassificationService


def test_classification_rules_context():
    """测试分类规则上下文生成"""
    print("=== 测试分类规则上下文生成 ===")
    
    db = next(get_db())
    ai_service = AIClassificationService()
    
    try:
        # 测试获取通用规则
        rules_context = ai_service.get_classification_rules_context(db)
        print("通用规则上下文:")
        print(rules_context)
        print()
        
        # 测试获取特定来源规则
        cmb_rules_context = ai_service.get_classification_rules_context(db, 'cmb')
        print("招商银行规则上下文:")
        print(cmb_rules_context)
        print()
        
        # 测试获取支付宝规则
        alipay_rules_context = ai_service.get_classification_rules_context(db, 'alipay')
        print("支付宝规则上下文:")
        print(alipay_rules_context)
        print()
        
    except Exception as e:
        print(f"测试失败: {e}")
    finally:
        db.close()


def test_single_bill_classification():
    """测试单个账单分类（包含规则）"""
    print("=== 测试单个账单分类 ===")
    
    db = next(get_db())
    ai_service = AIClassificationService()
    
    if not ai_service.is_available():
        print("AI分类服务不可用，跳过测试")
        db.close()
        return
    
    try:
        # 测试账单数据
        test_bills = [
            {
                'id': 1001,
                'transaction_type': '支出',
                'description': '滴滴出行-行程费用',
                'source_type': 'alipay'
            },
            {
                'id': 1002,
                'transaction_type': '支出',
                'description': '7-11便利店购物',
                'source_type': 'alipay'
            },
            {
                'id': 1003,
                'transaction_type': '支出',
                'description': '医院挂号费',
                'source_type': 'cmb'
            },
            {
                'id': 1004,
                'transaction_type': '收入',
                'description': '基金分红',
                'source_type': 'cmb'
            },
            {
                'id': 1005,
                'transaction_type': '支出',
                'description': '中石化加油站',
                'source_type': 'cmb'
            }
        ]
        
        print("测试单个账单分类:")
        for bill in test_bills:
            print(f"\n账单: {bill['description']} ({bill['transaction_type']})")
            category = ai_service.classify_single_bill(bill, db)
            print(f"分类结果: {category}")
        
    except Exception as e:
        print(f"测试失败: {e}")
    finally:
        db.close()


def test_batch_classification():
    """测试批量账单分类（包含规则）"""
    print("\n=== 测试批量账单分类 ===")
    
    db = next(get_db())
    ai_service = AIClassificationService()
    
    if not ai_service.is_available():
        print("AI分类服务不可用，跳过测试")
        db.close()
        return
    
    try:
        # 测试账单数据
        test_bills = [
            {
                'id': 2001,
                'transaction_type': '支出',
                'description': '滴滴出行-快车费用',
                'source_type': 'alipay'
            },
            {
                'id': 2002,
                'transaction_type': '支出',
                'description': '全家便利店',
                'source_type': 'alipay'
            },
            {
                'id': 2003,
                'transaction_type': '支出',
                'description': '药店购药',
                'source_type': 'cmb'
            },
            {
                'id': 2004,
                'transaction_type': '收入',
                'description': '股票分红',
                'source_type': 'cmb'
            },
            {
                'id': 2005,
                'transaction_type': '支出',
                'description': '地铁卡充值',
                'source_type': 'alipay'
            }
        ]
        
        print("测试批量账单分类:")
        results = ai_service.classify_bills_batch_optimized(test_bills, db, batch_size=5)
        
        print(f"\n批量分类结果 (共 {len(results)} 个):")
        for bill_id, category in results:
            bill = next((b for b in test_bills if b['id'] == bill_id), None)
            if bill:
                print(f"账单 {bill_id}: {bill['description']} -> {category}")
        
        # 统计分类成功率
        successful = sum(1 for _, category in results if category is not None)
        success_rate = (successful / len(results)) * 100 if results else 0
        print(f"\n分类成功率: {success_rate:.1f}% ({successful}/{len(results)})")
        
    except Exception as e:
        print(f"测试失败: {e}")
    finally:
        db.close()


def test_rules_priority():
    """测试规则优先级"""
    print("\n=== 测试规则优先级 ===")
    
    db = next(get_db())
    
    try:
        # 查看当前规则及其优先级
        rules = db.query(ClassificationRule).filter(
            ClassificationRule.is_active == True
        ).order_by(ClassificationRule.priority.desc()).all()
        
        print("当前启用的分类规则（按优先级排序）:")
        for rule in rules:
            print(f"优先级 {rule.priority}: {rule.rule_text} -> {rule.target_category} ({rule.source_type})")
        
        print(f"\n共 {len(rules)} 条规则")
        
    except Exception as e:
        print(f"测试失败: {e}")
    finally:
        db.close()


def main():
    """主测试函数"""
    print("开始测试AI分类服务集成分类规则功能\n")
    
    # 测试分类规则上下文生成
    test_classification_rules_context()
    
    # 测试规则优先级
    test_rules_priority()
    
    # 测试单个账单分类
    test_single_bill_classification()
    
    # 测试批量账单分类
    test_batch_classification()
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    main()