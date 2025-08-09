#!/usr/bin/env python3
"""
测试分类规则上下文生成功能
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(project_root, 'backend')
sys.path.insert(0, backend_path)

from config.database import get_db
from services.ai_classification_service import AIClassificationService


def main():
    """测试分类规则上下文生成"""
    print("=== 测试分类规则上下文生成 ===")
    
    db = next(get_db())
    ai_service = AIClassificationService()
    
    try:
        # 测试获取分类上下文
        print("1. 分类上下文:")
        categories_context = ai_service.get_categories_context(db)
        print(categories_context)
        print("\n" + "="*50 + "\n")
        
        # 测试获取通用规则
        print("2. 通用规则上下文:")
        rules_context = ai_service.get_classification_rules_context(db)
        print(rules_context)
        print("\n" + "="*50 + "\n")
        
        # 测试获取招商银行规则
        print("3. 招商银行规则上下文:")
        cmb_rules_context = ai_service.get_classification_rules_context(db, 'cmb')
        print(cmb_rules_context)
        print("\n" + "="*50 + "\n")
        
        # 测试完整提示词构建
        print("4. 完整提示词示例:")
        bill_data = {
            'id': 1001,
            'transaction_type': '支出',
            'description': '滴滴出行-行程费用',
            'source_type': 'alipay'
        }
        
        source_type = bill_data.get('source_type')
        rules_context = ai_service.get_classification_rules_context(db, source_type)
        
        bill_info = f"""账单信息：
- 账单ID: {bill_data.get('id', '未知')}
- 交易类型: {bill_data.get('transaction_type', '未知')}
- 描述: {bill_data.get('description', '无描述')}
- 来源: {bill_data.get('source_type', '未知')}"""
        
        prompt = f"""你是一个专业的账单分类助手。请根据账单信息为账单选择最合适的分类。

{categories_context}{rules_context}

分类指导：
1. **优先级顺序**：首先检查是否匹配分类规则，如果匹配则按规则分类；如果不匹配任何规则，再根据账单描述进行智能分类
2. **交易类型匹配**：根据交易类型选择对应类别
3. **关键词分析**：仔细分析账单描述中的关键词
4. **最佳匹配**：选择最具体、最相关的分类

{bill_info}

请按以下格式返回账单的分类结果：
账单ID: 分类名称 (ID: 分类ID)"""
        
        print(prompt)
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()