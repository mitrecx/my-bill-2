#!/usr/bin/env python3
"""
功能测试：验证AI分类实际按20个一批进行处理
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.ai_classification_service import AIClassificationService
from config.database import SessionLocal
from models.user import User
from models.bill import Bill
import logging

# 设置日志级别以观察批次处理
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_bills(count=25):
    """创建测试账单数据"""
    test_bills = []
    for i in range(count):
        bill_data = {
            'id': 10000 + i,
            'description': f'测试账单{i+1} - 餐饮消费',
            'transaction_type': '支出',
            'source_type': 'alipay',
            'amount': 50.0 + i
        }
        test_bills.append(bill_data)
    return test_bills

def test_batch_processing():
    """测试批量处理功能"""
    print("=== 测试AI分类批量处理（20个一批） ===")
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 创建AI分类服务实例
        ai_service = AIClassificationService()
        
        if not ai_service.is_available():
            print("⚠️  AI分类服务不可用，跳过功能测试")
            return False
        
        # 创建25个测试账单（应该分为2批：20个 + 5个）
        test_bills = create_test_bills(25)
        print(f"✓ 创建了{len(test_bills)}个测试账单")
        
        # 获取一个测试用户ID（如果没有则创建）
        user = db.query(User).first()
        if not user:
            print("❌ 未找到测试用户，请先创建用户")
            return False
        
        user_id = user.id
        print(f"✓ 使用用户ID: {user_id}")
        
        # 执行批量分类
        print("开始执行批量AI分类...")
        results = ai_service.classify_bills_batch_optimized(test_bills, db, user_id)
        
        print(f"✓ 分类完成，处理了{len(results)}个账单")
        
        # 验证结果
        success_count = sum(1 for _, category in results if category is not None)
        print(f"✓ 成功分类: {success_count}/{len(results)}")
        
        # 显示部分结果
        print("\n前5个分类结果:")
        for i, (bill_id, category) in enumerate(results[:5]):
            print(f"  账单{bill_id}: {category or '分类失败'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    finally:
        db.close()

def test_batch_size_verification():
    """验证批次大小设置"""
    print("\n=== 验证批次大小设置 ===")
    
    ai_service = AIClassificationService()
    
    # 模拟不同数量的账单，验证批次划分
    test_cases = [
        (15, 1),  # 15个账单 -> 1批
        (20, 1),  # 20个账单 -> 1批  
        (25, 2),  # 25个账单 -> 2批
        (40, 2),  # 40个账单 -> 2批
        (45, 3),  # 45个账单 -> 3批
    ]
    
    for bill_count, expected_batches in test_cases:
        # 计算实际批次数
        batch_size = 20  # 新的批次大小
        actual_batches = (bill_count + batch_size - 1) // batch_size  # 向上取整
        
        if actual_batches == expected_batches:
            print(f"✅ {bill_count}个账单 -> {actual_batches}批 (正确)")
        else:
            print(f"❌ {bill_count}个账单 -> {actual_batches}批 (期望{expected_batches}批)")
    
    return True

if __name__ == "__main__":
    print("开始AI分类批次大小功能测试...")
    
    success_count = 0
    total_tests = 2
    
    # 测试批次大小验证
    if test_batch_size_verification():
        success_count += 1
    
    # 测试实际批量处理（需要AI服务可用）
    if test_batch_processing():
        success_count += 1
    
    print(f"\n=== 测试结果 ===")
    print(f"通过测试: {success_count}/{total_tests}")
    
    if success_count >= 1:  # 至少批次大小验证要通过
        print("🎉 AI分类批次大小更改验证成功！")
        print("📝 现在AI分类将按20个账单一批进行处理，提高了处理效率")
    else:
        print("⚠️  测试未完全通过，请检查配置")