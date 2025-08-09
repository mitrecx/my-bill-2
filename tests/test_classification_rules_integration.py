#!/usr/bin/env python3
"""
测试分类规则集成功能
验证分类规则是否正确应用到账单分类中
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

from config.database import get_db
from models.bill import BillCategory
from models.classification_rule import ClassificationRule
from services.rule_classification_service import rule_classification_service
from services.ai_classification_service import ai_classification_service


def test_classification_rules():
    """测试分类规则功能"""
    print("=== 测试分类规则功能 ===")
    
    # 获取数据库连接
    db = next(get_db())
    
    try:
        # 1. 创建测试分类规则
        print("\n1. 创建测试分类规则...")
        
        # 删除可能存在的测试规则
        db.query(ClassificationRule).filter(
            ClassificationRule.rule_text.like('%测试规则%')
        ).delete()
        db.commit()
        
        # 创建测试规则
        test_rules = [
            {
                'rule_text': '关键词: 滴滴,打车,出租车',
                'source_type': 'cmb',
                'target_category': '交通出行',
                'priority': 10,
                'is_active': True
            },
            {
                'rule_text': '包含: 挂号费,医院,药费',
                'source_type': 'all',
                'target_category': '医疗保健',
                'priority': 8,
                'is_active': True
            },
            {
                'rule_text': '正则: .*基金.*',
                'source_type': 'cmb',
                'target_category': '投资收益',
                'priority': 5,
                'is_active': True
            }
        ]
        
        created_rules = []
        for rule_data in test_rules:
            rule = ClassificationRule(**rule_data)
            db.add(rule)
            created_rules.append(rule)
        
        db.commit()
        print(f"成功创建 {len(created_rules)} 条测试规则")
        
        # 2. 测试规则分类
        print("\n2. 测试规则分类...")
        
        test_bills = [
            {
                'id': 1001,
                'description': '滴滴出行-打车费用',
                'source_type': 'cmb',
                'transaction_type': '支出'
            },
            {
                'id': 1002,
                'description': '医院挂号费',
                'source_type': 'alipay',
                'transaction_type': '支出'
            },
            {
                'id': 1003,
                'description': '基金赎回到账',
                'source_type': 'cmb',
                'transaction_type': '收入'
            },
            {
                'id': 1004,
                'description': '超市购物',
                'source_type': 'cmb',
                'transaction_type': '支出'
            }
        ]
        
        for bill in test_bills:
            category = rule_classification_service.apply_classification_rules(bill, db)
            print(f"账单 {bill['id']} ({bill['description']}) -> {category or '无匹配规则'}")
        
        # 3. 测试AI分类服务集成
        print("\n3. 测试AI分类服务集成...")
        
        # 测试单个账单分类
        for bill in test_bills:
            category = ai_classification_service.classify_single_bill(bill, db)
            print(f"AI分类 - 账单 {bill['id']} ({bill['description']}) -> {category or '分类失败'}")
        
        # 测试批量分类
        print("\n4. 测试批量分类...")
        batch_results = ai_classification_service.classify_bills_batch_optimized(test_bills, db)
        for bill_id, category in batch_results:
            bill = next(b for b in test_bills if b['id'] == bill_id)
            print(f"批量分类 - 账单 {bill_id} ({bill['description']}) -> {category or '分类失败'}")
        
        # 5. 测试规则统计
        print("\n5. 测试规则统计...")
        stats = rule_classification_service.get_rule_statistics(db)
        print(f"规则统计: {stats}")
        
        # 6. 清理测试数据
        print("\n6. 清理测试数据...")
        for rule in created_rules:
            db.delete(rule)
        db.commit()
        print("测试数据清理完成")
        
        print("\n=== 分类规则功能测试完成 ===")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def test_rule_formats():
    """测试不同的规则格式"""
    print("\n=== 测试规则格式 ===")
    
    db = next(get_db())
    
    try:
        # 测试不同格式的规则
        test_cases = [
            {
                'rule_text': '关键词: 滴滴,打车',
                'description': '滴滴出行费用',
                'expected': True
            },
            {
                'rule_text': '包含: 医院,挂号',
                'description': '医院挂号费',
                'expected': True
            },
            {
                'rule_text': '正则: ^.*基金.*$',
                'description': '基金赎回',
                'expected': True
            },
            {
                'rule_text': '超市',
                'description': '超市购物',
                'expected': True
            },
            {
                'rule_text': '关键词: 滴滴',
                'description': '超市购物',
                'expected': False
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            # 创建临时规则
            rule = ClassificationRule(
                rule_text=case['rule_text'],
                source_type='all',
                target_category='测试分类',
                priority=1,
                is_active=True
            )
            
            # 测试匹配
            service = rule_classification_service
            matches = service._rule_matches(rule, case['description'], '支出', db)
            
            status = "✓" if matches == case['expected'] else "✗"
            print(f"{status} 测试 {i}: 规则 '{case['rule_text']}' 匹配 '{case['description']}' -> {matches}")
        
        print("=== 规则格式测试完成 ===")
        
    except Exception as e:
        print(f"规则格式测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_classification_rules()
    test_rule_formats()