#!/usr/bin/env python3
"""
测试AI分类服务使用分类规则功能
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(project_root, 'backend')
sys.path.insert(0, backend_path)

from config.database import get_db
from services.ai_classification_service import AIClassificationService


def test_single_classification():
    """测试单个账单分类"""
    print("=== 测试单个账单AI分类（包含规则） ===")
    
    db = next(get_db())
    ai_service = AIClassificationService()
    
    if not ai_service.is_available():
        print("AI分类服务不可用，跳过测试")
        db.close()
        return
    
    try:
        # 测试应该匹配规则的账单
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
                'transaction_type': '收入',
                'description': '基金分红收入',
                'source_type': 'cmb'
            }
        ]
        
        print("测试账单分类:")
        for bill in test_bills:
            print(f"\n账单: {bill['description']} ({bill['transaction_type']})")
            print(f"来源: {bill['source_type']}")
            
            category = ai_service.classify_single_bill(bill, db)
            print(f"分类结果: {category}")
            
            # 检查是否符合预期
            expected = None
            if '滴滴' in bill['description']:
                expected = '交通出行'
            elif '7-11' in bill['description'] or '便利店' in bill['description']:
                expected = '日用百货'
            elif '基金' in bill['description'] and bill['transaction_type'] == '收入':
                expected = '投资收益'
            
            if expected and category == expected:
                print(f"✓ 符合预期规则: {expected}")
            elif expected:
                print(f"✗ 不符合预期规则: 期望 {expected}, 实际 {category}")
            else:
                print(f"? 无明确规则，AI智能分类: {category}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def test_batch_classification():
    """测试批量账单分类"""
    print("\n=== 测试批量账单AI分类（包含规则） ===")
    
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
                'description': '滴滴快车费用',
                'source_type': 'alipay'
            },
            {
                'id': 2002,
                'transaction_type': '支出',
                'description': '全家便利店购物',
                'source_type': 'alipay'
            },
            {
                'id': 2003,
                'transaction_type': '支出',
                'description': '医院挂号费',
                'source_type': 'cmb'
            }
        ]
        
        print("测试批量账单分类:")
        results = ai_service.classify_bills_batch_optimized(test_bills, db, batch_size=3)
        
        print(f"\n批量分类结果:")
        for bill_id, category in results:
            bill = next((b for b in test_bills if b['id'] == bill_id), None)
            if bill:
                print(f"账单 {bill_id}: {bill['description']} -> {category}")
                
                # 检查是否符合预期
                expected = None
                if '滴滴' in bill['description']:
                    expected = '交通出行'
                elif '全家' in bill['description'] or '便利店' in bill['description']:
                    expected = '日用百货'
                elif '医院' in bill['description'] or '挂号' in bill['description']:
                    expected = '医疗保健'
                
                if expected and category == expected:
                    print(f"  ✓ 符合预期规则: {expected}")
                elif expected:
                    print(f"  ✗ 不符合预期规则: 期望 {expected}, 实际 {category}")
                else:
                    print(f"  ? 无明确规则，AI智能分类: {category}")
        
        # 统计分类成功率
        successful = sum(1 for _, category in results if category is not None)
        success_rate = (successful / len(results)) * 100 if results else 0
        print(f"\n分类成功率: {success_rate:.1f}% ({successful}/{len(results)})")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def main():
    """主测试函数"""
    print("开始测试AI分类服务使用分类规则功能\n")
    
    # 测试单个账单分类
    test_single_classification()
    
    # 测试批量账单分类
    test_batch_classification()
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    main()