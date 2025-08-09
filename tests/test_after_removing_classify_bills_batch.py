#!/usr/bin/env python3
"""
测试删除 classify_bills_batch 方法后的AI分类服务功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.services.ai_classification_service import ai_classification_service
from backend.database import get_db
from backend.models.bill_category import BillCategory

def test_ai_classification_service_methods():
    """测试AI分类服务的可用方法"""
    print("=== 测试AI分类服务方法 ===")
    
    # 检查服务是否可用
    print(f"AI分类服务可用性: {ai_classification_service.is_available()}")
    
    # 检查可用的方法
    methods = [method for method in dir(ai_classification_service) if not method.startswith('_') and callable(getattr(ai_classification_service, method))]
    print(f"可用方法: {methods}")
    
    # 确认 classify_bills_batch 方法已被删除
    has_classify_bills_batch = hasattr(ai_classification_service, 'classify_bills_batch')
    print(f"是否还有 classify_bills_batch 方法: {has_classify_bills_batch}")
    
    # 确认 classify_bills_batch_optimized 方法存在
    has_classify_bills_batch_optimized = hasattr(ai_classification_service, 'classify_bills_batch_optimized')
    print(f"是否有 classify_bills_batch_optimized 方法: {has_classify_bills_batch_optimized}")
    
    # 确认 classify_single_bill 方法存在
    has_classify_single_bill = hasattr(ai_classification_service, 'classify_single_bill')
    print(f"是否有 classify_single_bill 方法: {has_classify_single_bill}")

def test_optimized_batch_classification():
    """测试优化的批量分类功能"""
    print("\n=== 测试优化的批量分类功能 ===")
    
    if not ai_classification_service.is_available():
        print("AI分类服务不可用，跳过测试")
        return
    
    # 模拟账单数据
    test_bills = [
        {
            'id': 1001,
            'transaction_type': '支出',
            'description': '滴滴出行-打车费用',
            'source_type': 'cmb'
        },
        {
            'id': 1002,
            'transaction_type': '支出',
            'description': '星巴克咖啡',
            'source_type': 'cmb'
        }
    ]
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 测试优化的批量分类
        results = ai_classification_service.classify_bills_batch_optimized(test_bills, db)
        print(f"批量分类结果: {results}")
        
        # 测试单个分类
        single_result = ai_classification_service.classify_single_bill(test_bills[0], db)
        print(f"单个分类结果: {single_result}")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
    finally:
        db.close()

def test_categories_context():
    """测试分类上下文获取功能"""
    print("\n=== 测试分类上下文获取功能 ===")
    
    db = next(get_db())
    
    try:
        # 测试获取分类上下文
        context = ai_classification_service.get_categories_context(db)
        print(f"分类上下文长度: {len(context) if context else 0}")
        if context:
            print(f"分类上下文前200字符: {context[:200]}...")
        
        # 检查数据库中的分类数量
        categories_count = db.query(BillCategory).count()
        print(f"数据库中的分类数量: {categories_count}")
        
    except Exception as e:
        print(f"获取分类上下文时出现错误: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("开始测试删除 classify_bills_batch 方法后的AI分类服务...")
    
    test_ai_classification_service_methods()
    test_categories_context()
    test_optimized_batch_classification()
    
    print("\n测试完成！")