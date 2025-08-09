#!/usr/bin/env python3
"""
测试优化后的AI分类提示词
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from config.database import SessionLocal
from services.ai_classification_service import AIClassificationService
from models import BillCategory

def test_optimized_prompt():
    """测试优化后的提示词"""
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 创建AI分类服务实例
        ai_service = AIClassificationService()
        
        # 测试不同来源的账单数据
        test_bills = [
            {
                'id': 12001,
                'transaction_type': '支出',
                'description': '网联清算-财付通-滴滴出行',
                'source_type': 'cmb'
            },
            {
                'id': 12002,
                'transaction_type': '支出', 
                'description': '收钱吧-美团外卖',
                'source_type': 'alipay'
            },
            {
                'id': 12003,
                'transaction_type': '支出',
                'description': '京东商城购物 | 数码配件',
                'source_type': 'jd'
            }
        ]
        
        print("=== 测试优化后的AI分类提示词 ===\n")
        
        # 测试单个分类
        print("1. 测试单个分类:")
        for bill in test_bills:
            print(f"\n测试账单: {bill}")
            
            # 获取分类上下文
            categories_context = ai_service.get_categories_context(db)
            print(f"分类上下文长度: {len(categories_context)} 字符")
            
            # 获取分类规则上下文
            rules_context = ai_service.get_classification_rules_context(db, bill['source_type'])
            print(f"分类规则上下文长度: {len(rules_context)} 字符")
            
            # 获取描述字段信息
            description_info = ai_service.get_description_field_info(bill['source_type'])
            print(f"描述字段信息: {description_info.strip()}")
            
            # 如果AI服务可用，进行实际分类
            if ai_service.is_available():
                result = ai_service.classify_single_bill(bill, db)
                print(f"分类结果: {result}")
            else:
                print("AI服务不可用，跳过实际分类")
        
        # 测试批量分类
        print(f"\n2. 测试批量分类:")
        print(f"批量账单数量: {len(test_bills)}")
        
        if ai_service.is_available():
            batch_results = ai_service.classify_bills_batch_optimized(test_bills, db, batch_size=3)
            print(f"批量分类结果: {batch_results}")
        else:
            print("AI服务不可用，跳过批量分类")
        
        # 测试不同来源类型的规则获取
        print(f"\n3. 测试不同来源类型的规则获取:")
        for source_type in ['cmb', 'alipay', 'jd']:
            rules = ai_service.get_classification_rules_context(db, source_type)
            description = ai_service.get_description_field_info(source_type)
            print(f"\n{source_type} 来源:")
            print(f"  规则数量: {rules.count('如果账单描述包含') if rules else 0}")
            print(f"  描述信息: {description.strip()}")
        
        print(f"\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_optimized_prompt()