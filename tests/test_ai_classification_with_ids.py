#!/usr/bin/env python3
"""
测试AI分类服务的修改：
1. 验证分类上下文中包含分类ID
2. 验证提示词中不包含金额字段
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

from services.ai_classification_service import AIClassificationService
from config.database import get_db
from models.bill import BillCategory
from sqlalchemy.orm import Session

def test_categories_context_includes_ids():
    """测试分类上下文是否包含分类ID"""
    print("测试分类上下文是否包含分类ID...")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 创建AI分类服务实例
        ai_service = AIClassificationService()
        
        # 获取分类上下文
        context = ai_service.get_categories_context(db)
        
        print("分类上下文内容:")
        print(context)
        print()
        
        # 检查是否包含ID信息
        if "ID:" in context:
            print("✅ 分类上下文包含分类ID")
        else:
            print("❌ 分类上下文不包含分类ID")
            
        # 获取数据库中的分类数据进行验证
        categories = db.query(BillCategory).all()
        print(f"数据库中共有 {len(categories)} 个分类")
        
        for category in categories[:3]:  # 只显示前3个分类
            expected_text = f"ID: {category.id}"
            if expected_text in context:
                print(f"✅ 分类 '{category.category_name}' (ID: {category.id}) 在上下文中")
            else:
                print(f"❌ 分类 '{category.category_name}' (ID: {category.id}) 不在上下文中")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        db.close()

def test_prompt_excludes_amount():
    """测试提示词是否不包含金额字段"""
    print("\n测试提示词是否不包含金额字段...")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 创建AI分类服务实例
        ai_service = AIClassificationService()
        
        # 模拟账单数据
        test_bill = {
            'id': 12345,
            'amount': 100.50,
            'transaction_type': '支出',
            'description': '测试账单描述',
            'source_type': 'cmb'
        }
        
        # 构建单个账单分类的提示词
        categories_context = ai_service.get_categories_context(db)
        
        prompt = f"""你是一个专业的账单分类助手。请根据账单信息将其分类到合适的类别中。

可用的账单分类：
{categories_context}

请分析以下账单信息：
- 交易类型: {test_bill.get('transaction_type', '未知')}
- 描述: {test_bill.get('description', '无描述')}
- 来源: {test_bill.get('source_type', '未知')}

请返回最合适的分类名称（只返回分类名称，不要其他内容）："""
        
        print("单个账单分类提示词:")
        print(prompt)
        print()
        
        # 检查是否包含金额字段
        if "金额:" in prompt or "amount" in prompt.lower():
            print("❌ 提示词包含金额字段")
        else:
            print("✅ 提示词不包含金额字段")
            
        # 测试批量分类提示词
        test_bills = [test_bill]
        bills_info = []
        for bill in test_bills:
            bill_info = f"""账单ID: {bill.get('id')}
   - 交易类型: {bill.get('transaction_type', '未知')}
   - 描述: {bill.get('description', '无描述')}
   - 来源: {bill.get('source_type', '未知')}"""
            bills_info.append(bill_info)
        
        batch_prompt = f"""你是一个专业的账单分类助手。请根据账单信息将每个账单分类到合适的类别中。

可用的账单分类：
{categories_context}

请分析以下账单信息：
{chr(10).join(bills_info)}

请为每个账单返回最合适的分类名称，格式为：
账单ID: 分类名称

只返回分类结果，不要其他内容："""
        
        print("批量账单分类提示词:")
        print(batch_prompt)
        print()
        
        # 检查批量提示词是否包含金额字段
        if "金额:" in batch_prompt or "amount" in batch_prompt.lower():
            print("❌ 批量提示词包含金额字段")
        else:
            print("✅ 批量提示词不包含金额字段")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        db.close()

def test_suggest_rule_excludes_amount():
    """测试分类规则建议是否不包含金额字段"""
    print("\n测试分类规则建议是否不包含金额字段...")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 创建AI分类服务实例
        ai_service = AIClassificationService()
        
        # 模拟账单数据
        test_bill = {
            'id': 12345,
            'amount': 100.50,
            'transaction_type': '支出',
            'description': '滴滴出行打车费',
            'source_type': 'cmb'
        }
        
        # 构建分类规则建议的提示词
        prompt = f"""基于以下账单信息和分类结果，请生成一个简洁的分类规则：

账单信息：
- 交易类型: {test_bill.get('transaction_type', '未知')}
- 描述: {test_bill.get('description', '无描述')}
- 来源: {test_bill.get('source_type', '未知')}

分类结果: 交通出行

请生成一个简洁的分类规则，用于自动识别类似的账单。规则应该：
1. 基于账单描述中的关键词
2. 简洁明了，易于理解
3. 具有一定的通用性

分类规则："""
        
        print("分类规则建议提示词:")
        print(prompt)
        print()
        
        # 检查是否包含金额字段
        if "金额:" in prompt or "amount" in prompt.lower():
            print("❌ 分类规则建议提示词包含金额字段")
        else:
            print("✅ 分类规则建议提示词不包含金额字段")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("开始测试AI分类服务的修改...")
    print("=" * 50)
    
    test_categories_context_includes_ids()
    test_prompt_excludes_amount()
    test_suggest_rule_excludes_amount()
    
    print("\n" + "=" * 50)
    print("测试完成!")