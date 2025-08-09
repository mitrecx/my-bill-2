#!/usr/bin/env python3
"""
测试AI批量分类解析逻辑修复
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.ai_classification_service import AIClassificationService
from config.database import SessionLocal
from models.bill import BillCategory

def test_parsing_logic():
    """测试解析逻辑"""
    print("=== 测试AI批量分类解析逻辑修复 ===")
    
    # 创建AI分类服务实例
    ai_service = AIClassificationService()
    
    # 创建数据库连接
    db = SessionLocal()
    
    try:
        # 模拟AI返回的响应（与日志中的格式一致）
        ai_response = """账单ID: 13082: 2
账单ID: 13083: 10
账单ID: 13084: 11"""
        
        # 模拟账单数据
        bills_batch = [
            {'id': 13082, 'description': '测试账单1'},
            {'id': 13083, 'description': '测试账单2'},
            {'id': 13084, 'description': '测试账单3'}
        ]
        
        print(f"模拟AI响应:\n{ai_response}")
        print(f"\n账单数据: {bills_batch}")
        
        # 测试解析
        results = ai_service._parse_batch_classification_result(ai_response, bills_batch, db, 1)
        
        print(f"\n解析结果:")
        for bill_id, category_name in results:
            print(f"  账单ID {bill_id}: {category_name}")
        
        # 验证结果
        expected_bill_ids = {13082, 13083, 13084}
        actual_bill_ids = {bill_id for bill_id, _ in results}
        
        if expected_bill_ids == actual_bill_ids:
            print("\n✅ 解析成功：所有账单ID都被正确解析")
        else:
            print(f"\n❌ 解析失败：期望 {expected_bill_ids}，实际 {actual_bill_ids}")
        
        # 检查是否有分类名称
        categories_found = sum(1 for _, category_name in results if category_name is not None)
        print(f"找到分类的账单数量: {categories_found}/{len(results)}")
        
        # 测试其他格式
        print("\n=== 测试其他格式 ===")
        
        # 测试简单格式
        simple_response = """13082: 2
13083: 10
13084: 11"""
        
        print(f"简单格式响应:\n{simple_response}")
        simple_results = ai_service._parse_batch_classification_result(simple_response, bills_batch, db, 1)
        
        print(f"\n简单格式解析结果:")
        for bill_id, category_name in simple_results:
            print(f"  账单ID {bill_id}: {category_name}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_parsing_logic()